#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import paramiko
from apps.models.logger_manager import LoggerManager


class SSHExecutor:
    def __init__(self, client_info, output_queue, logger=None):
        self.client_info = client_info
        self.output_queue = output_queue
        self.logger = logger or LoggerManager()
        self.ssh = paramiko.SSHClient()

    def connect(self):
        """建立SSH连接（支持密钥和密码认证）"""
        try:
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if 'key_path' in self.client_info and self.client_info['key_path']:
                # 密钥认证
                private_key = paramiko.RSAKey.from_private_key_file(
                    self.client_info['key_path']
                )
                self.ssh.connect(
                    hostname=self.client_info['ip'],
                    port=self.client_info['port'],
                    username=self.client_info['user'],
                    pkey=private_key,
                    timeout=10
                )
            else:
                # 密码认证
                self.ssh.connect(
                    hostname=self.client_info['ip'],
                    port=self.client_info['port'],
                    username=self.client_info['user'],
                    password=self.client_info.get('password', ''),
                    timeout=10
                )

            self.logger.info(f"成功连接到服务器 {self.client_info['ip']}")
            return True
        except Exception as e:
            err_msg = f"SSH连接失败: {str(e)}"
            self.logger.error(err_msg)
            self.output_queue.put({
                "status": "error",
                "message": err_msg
            })
            return False

    def execute_command(self, command):
        """执行远程命令并实时捕获输出到队列"""
        try:
            stdin, stdout, stderr = self.ssh.exec_command(command)

            # 实时读取标准输出
            for line in iter(stdout.readline, ""):
                line = line.strip()
                if line:
                    self.output_queue.put({
                        "status": "output",
                        "message": line
                    })

            # 读取标准错误
            err_lines = stderr.read().strip()
            if err_lines:
                error_msg = f"命令执行错误: {err_lines}"
                self.output_queue.put({
                    "status": "error",
                    "message": error_msg
                })
                self.logger.error(error_msg)
            else:
                self.output_queue.put({
                    "status": "success",
                    "message": "远程命令执行完成"
                })

        except Exception as e:
            err_msg = f"执行远程命令失败: {str(e)}"
            self.logger.error(err_msg)
            self.output_queue.put({
                "status": "error",
                "message": err_msg
            })
        finally:
            # 确保连接关闭
            if self.ssh.get_transport() and self.ssh.get_transport().is_active():
                self.ssh.close()
            # 放入终止信号
            self.output_queue.put(None)
