#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import threading


class ExecutionStats:
    """执行统计管理器（线程安全）"""
    def __init__(self):
        self.lock = threading.Lock()  # 线程安全锁
        # 总体统计
        self.total_executions = 0  # 总执行次数（脚本+命令）
        self.total_failures = 0    # 总失败次数（脚本+命令）
        # 按任务ID统计（脚本任务）
        self.task_stats = {}  # 格式: {task_id: {'executions': int, 'failures': int}}
        # 命令执行统计
        self.cmd_stats = {'executions': 0, 'failures': 0}

    def reset(self):
        """重置所有统计数据（线程安全）"""
        with self.lock:
            self.total_executions = 0
            self.total_failures = 0
            self.task_stats = {}
            self.cmd_stats = {'executions': 0, 'failures': 0}

    def increment_execution(self, task_id=None, is_command=False):
        """增加执行次数"""
        with self.lock:
            self.total_executions += 1
            if is_command:
                self.cmd_stats['executions'] += 1
            else:
                if task_id not in self.task_stats:
                    self.task_stats[task_id] = {'executions': 0, 'failures': 0}
                self.task_stats[task_id]['executions'] += 1

    def increment_failure(self, task_id=None, is_command=False):
        """增加失败次数"""
        with self.lock:
            self.total_failures += 1
            if is_command:
                self.cmd_stats['failures'] += 1
            else:
                if task_id not in self.task_stats:
                    self.task_stats[task_id] = {'executions': 0, 'failures': 0}
                self.task_stats[task_id]['failures'] += 1

    def get_stats(self):
        """获取当前统计数据（副本，避免线程安全问题）"""
        with self.lock:
            return {
                "total_executions": self.total_executions,
                "total_failures": self.total_failures,
                "task_stats": self.task_stats.copy(),
                "cmd_stats": self.cmd_stats.copy()
            }

# 全局单例统计实例
stats_manager = ExecutionStats()
