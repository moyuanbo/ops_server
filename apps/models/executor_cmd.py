#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import subprocess
import queue
import time
from typing import Optional, Dict, List

# 导入统计管理器
from apps.models.execution_stats import stats_manager


def _split_output(output: str, is_error: bool) -> List[Dict]:
    """
    将输出按行分割为前端消息格式
    :param output: 命令输出（stdout或stderr）
    :param is_error: 是否为错误输出
    :return: 消息列表（每条消息符合前端格式）
    """
    """分割输出为前端消息格式"""
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return [{"status": "error" if is_error else "info", "message": line} for line in lines]


class BatchCommandExecutor:
    """批量命令执行器：执行命令时缓存所有输出，完成后统一推送到前端队列"""

    def __init__(self, output_queue: queue.Queue, logger, default_timeout: Optional[int] = None):
        """
        初始化批量命令执行器
        :param output_queue: 前端输出队列（命令完成后推送结果）
        :param logger: 日志实例（用于写入日志文件）
        :param default_timeout: 默认超时时间（秒）
        """
        self.output_queue = output_queue  # 前端输出队列
        self.default_timeout = default_timeout  # 默认超时
        self.logger = logger  # 日志实例（关键：用于记录到文件）
        self.proc = None

    def _cleanup(self):
        """清理进程资源"""
        if self.proc and self.proc.poll() is None:
            self.proc.kill()

    def execute(self, cmd: str, display: bool = False, timeout: Optional[int] = None) -> Dict:
        """
        执行命令，缓存输出，完成后统一推送
        :param display: 默认打印信息到前端
        :param cmd: 命令字符串
        :param timeout: 本次命令超时时间（优先级高于默认）
        :return: 包含stdout/stderr的结果字典
        """
        result = {
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": "",
            "error": None
        }
        timeout = timeout or self.default_timeout
        start_time = time.strftime("%Y-%m-%d %H:%M:%S")  # 记录开始时间

        # 1. 记录命令开始执行（日志文件）
        self.logger.info(f"[命令开始] 时间: {start_time} | 命令: {cmd} | 超时: {timeout or '无限制'}秒")

        try:
            # 记录命令执行，增加执行次数
            stats_manager.increment_execution(is_command=True)
            self.proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # 获取完整输出
            stdout, stderr = self.proc.communicate(timeout=timeout)
            result["stdout"] = stdout.strip()
            result["stderr"] = stderr.strip()
            end_time = time.strftime("%Y-%m-%d %H:%M:%S")  # 记录结束时间

            # 错误直接推送信息到前端；正确信息默认不输出到前端，当display=True时才输出到前端
            if display:
                for msg in _split_output(stdout, is_error=False):
                    self.output_queue.put(msg)
            for msg in _split_output(stderr, is_error=True):
                self.output_queue.put(msg)

            # 3. 记录命令执行结果（日志文件）
            self.logger.info(
                f"[命令完成] 时间: {end_time} | 返回码: {self.proc.returncode} | "
                f"成功: {self.proc.returncode == 0}\n"
                f"标准输出:\n{stdout.strip() or '无'}\n"
                f"错误输出:\n{stderr.strip() or '无'}"
            )

            # 更新执行状态
            result["return_code"] = self.proc.returncode
            result["success"] = self.proc.returncode == 0

        except subprocess.TimeoutExpired as e:
            end_time = time.strftime("%Y-%m-%d %H:%M:%S")
            result["error"] = f"命令超时（{timeout}秒）: {str(e)}"
            # 超时后获取已输出内容
            if self.proc and self.proc.poll() is None:
                self.proc.kill()
                stdout, stderr = self.proc.communicate()
                result["stdout"] = stdout.strip() if stdout else ""
                result["stderr"] = stderr.strip() if stderr else ""

                # 错误直接推送信息到前端；正确信息默认输出到前端，当display=False时不输出到前端
                if not display:
                    for msg in _split_output(stdout, is_error=False):
                        self.output_queue.put(msg)
                for msg in _split_output(stderr, is_error=True):
                    self.output_queue.put(msg)
            # 推送超时信息到前端
            self.output_queue.put({"status": "error", "message": result["error"]})
            # 记录超时日志（日志文件）
            self.logger.error(
                f"[命令超时] 时间: {end_time} | 命令: {cmd}\n"
                f"超时前输出:\n{result['stdout'] or '无'}\n"
                f"超时前错误:\n{result['stderr'] or '无'}\n"
                f"错误信息: {result['error']}"
            )

        except FileNotFoundError as e:
            result["error"] = f"命令不存在: {str(e)}"
            self.output_queue.put({"status": "error", "message": result["error"]})
            self.logger.error(f"[命令错误] 命令: {cmd} | 错误: {result['error']}")  # 记录日志

        except Exception as e:
            result["error"] = f"执行失败: {str(e)}"
            self.output_queue.put({"status": "error", "message": result["error"]})
            self.logger.error(f"[执行异常] 命令: {cmd} | 异常: {result['error']}")  # 记录日志

        finally:
            self._cleanup()
            self.proc = None

        # 命令执行失败时，增加失败次数
        if not result["success"]:
            stats_manager.increment_failure(is_command=True)

        return result
