#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import time
import json
import threading
from queue import Queue

# 导入统计管理器
from apps.models.execution_stats import stats_manager


class ExecutorScript:
    def __init__(self):
        self.output_queue = Queue()  # 线程安全队列
        self.lock = threading.Lock()  # 保证线程安全

    def executor_shell(self, logger, script, parameter, info, executor_scripts, task_id):
        """执行脚本并实时将输出写入队列（逻辑不变，增加日志）"""
        try:
            # 1. 记录任务开始，增加执行次数
            stats_manager.increment_execution(task_id=task_id, is_command=False)
            # 1. 发送任务开始信息
            self.output_queue.put({
                "task_id": task_id,
                "status": "start",
                "message": info
            })
            logger.info(f"任务[{task_id}]已加入队列，开始执行")

            # 2. 执行脚本（用subprocess实时捕获输出）
            import subprocess
            script_file = executor_scripts.get(script, executor_scripts[f'default_script'])
            cmd = f"bash {script_file} {parameter}"  # 脚本路径+参数
            start_time = time.strftime("%Y-%m-%d %H:%M:%S")  # 记录开始时间
            logger.info(f"[命令开始] 时间: {start_time} | 命令: {cmd}")
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1  # 行缓冲，实时输出
            )

            # 3. 实时读取输出并写入队列
            for line in process.stdout:
                self.output_queue.put({
                    "task_id": task_id,
                    "status": "running",
                    "message": line.strip()
                })

            # 4. 任务完成后判断结果，更新失败统计
            process.wait()
            if process.returncode == 0:
                self.output_queue.put({
                    "task_id": task_id,
                    "status": "success",
                    "message": f"任务完成（返回码：{process.returncode}）"
                })
            else:
                # 脚本执行失败，增加失败次数
                stats_manager.increment_failure(task_id=task_id, is_command=False)
                self.output_queue.put({
                    "task_id": task_id,
                    "status": "failed",
                    "message": f"任务失败（返回码：{process.returncode}）"
                })
            logger.info(f"任务[{task_id}]执行完毕，返回码：{process.returncode}")

        except Exception as e:
            # 执行异常，增加失败次数
            stats_manager.increment_failure(task_id=task_id, is_command=False)
            error_msg = f"执行异常：{str(e)}"
            self.output_queue.put({
                "task_id": task_id,
                "status": "error",
                "message": error_msg
            })
            logger.error(f"任务[{task_id}]异常：{error_msg}")

    def get_output_generator(self, logger):
        """生成SSE格式的输出流（修复语法错误，增加日志）"""
        logger.info("开始输出流生成器")
        while True:
            try:
                item = self.output_queue.get()  # 阻塞等待队列数据
                logger.info(f"从队列获取数据：{item}")

                if item is None:  # 收到终止信号
                    logger.info("收到终止信号，输出所有任务完成信息")
                    yield "data: {\"status\": \"completed\", \"message\": \"所有任务执行完毕\"}\n\n"
                    break

                # 转换为JSON并按SSE格式输出
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"

            except Exception as e:
                logger.error(f"输出流生成异常：{str(e)}")
                yield f"data: {{\"status\": \"error\", \"message\": \"输出流异常：{str(e)}\"}}\n\n"
