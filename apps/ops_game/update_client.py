#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json
import queue
from concurrent.futures import ThreadPoolExecutor
from apps.models.logger_manager import LoggerManager
from apps.models.executor_ssh import SSHExecutor
from apps.config import CLIENT_INFO, CLIENT_UPDATE_CMD, MAX_WORKERS


class UpdateClientApp:
    def __init__(self):
        self.logger = LoggerManager()
        self.output_queue = queue.Queue()  # 线程安全的输出队列
        self.task_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        # 初始化SSH执行器
        self.ssh_executor = SSHExecutor(
            client_info=CLIENT_INFO,
            output_queue=self.output_queue,
            logger=self.logger
        )

    def start_update(self, channel):
        """
        开始前端更新流程（生成SSE流，实时返回日志）
        :param channel: 前端传入的更新渠道（Wechat/indexIos/ALL）
        """
        # 1. 校验渠道参数是否合法
        if channel not in CLIENT_UPDATE_CMD:
            err_msg = f"不支持的更新渠道：{channel}，支持的渠道：{list(CLIENT_UPDATE_CMD.keys())}"
            self.logger.error(err_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': err_msg})}\n\n"
            return

        # 2. 建立SSH连接
        yield f"data: {json.dumps({'status': 'loading', 'message': '正在建立SSH连接...'})}\n\n"
        if not self.ssh_executor.connect():
            err_msg = 'SSH连接失败，启动更新失败'
            self.logger.error(err_msg)
            yield f"data: {json.dumps({'status': 'error', 'message': err_msg})}\n\n"
            return

        # 3. 获取对应渠道的更新命令
        update_cmd = CLIENT_UPDATE_CMD[channel]
        self.logger.info(f"执行{channel}渠道更新命令：{update_cmd}")
        yield f"data: {json.dumps({'status': 'loading', 'message': f'开始执行{channel}渠道更新命令...'})}\n\n"

        # 4. 提交远程命令执行任务（异步）
        self.task_pool.submit(
            self.ssh_executor.execute_command,
            update_cmd  # 传入匹配的渠道命令
        )

        # 5. 实时读取输出队列并推送给前端（SSE）
        while True:
            try:
                item = self.output_queue.get(timeout=30)  # 超时避免无限阻塞
                if item is None:
                    # 任务完成
                    yield f"data: {json.dumps({'status': 'completed', 'message': f'{channel}渠道前端更新操作全部完成'})}\n\n"
                    break
                # 推送输出内容（兼容原有SSH执行器的输出格式）
                if isinstance(item, dict):
                    yield f"data: {json.dumps(item)}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'loading', 'message': str(item)})}\n\n"
            except queue.Empty:
                # 心跳包避免连接断开
                yield f"data: {json.dumps({'status': 'heartbeat', 'message': '等待命令执行输出...'})}\n\n"
            except Exception as e:
                err_msg = f"推送日志异常: {str(e)}"
                self.logger.error(err_msg)
                yield f"data: {json.dumps({'status': 'error', 'message': err_msg})}\n\n"
                break

        # 关闭线程池
        self.task_pool.shutdown(wait=True)
