#!/usr/bin/env python3
# -*- coding: UTF-8 -*-


class TaskUtil:
    """任务处理工具类"""
    @staticmethod
    def generate_task_id(channel, game_type, game_nu):
        """生成统一的任务ID"""
        return f"{channel}_{game_type}_{game_nu}"

    @staticmethod
    def generate_task_info(channel, game_type, game_nu, game_ip, operation_desc):
        """生成任务描述信息"""
        return (f"操作信息: IP={game_ip}, 渠道={channel}, 类型={game_type}, "
                f"区服={game_nu}, 操作={operation_desc}")