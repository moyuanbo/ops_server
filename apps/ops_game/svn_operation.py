#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import ast
import os
from apps.config import SVN_CONFIG
from apps.models.query_channel_svn_bin import channel_svn_bin
from apps.ops_game.db_utils import GameDBUtil


def execute_command(cmd_executor, cmd, logger, output_queue, error_msg_prefix):
    """
    通用命令执行函数，处理命令执行、结果判断、错误日志和前端消息

    :param cmd_executor: 命令执行器实例
    :param cmd: 待执行的命令
    :param logger: 日志实例
    :param output_queue: 前端输出队列
    :param error_msg_prefix: 错误提示前缀（如"创建目录失败"）
    :return: 成功返回(status_info, True)，失败返回(错误信息, False)
    """
    status_info = cmd_executor.execute(cmd)
    if not status_info["success"]:
        error_detail = status_info["error"] or status_info["stderr"]
        error_msg = f"{error_msg_prefix}: {error_detail}"
        logger.error(error_msg)
        output_queue.put({"status": "error", "message": error_msg})
        return error_msg, False
    return status_info, True


def svn_update(svn_logger, executor):
    """
    执行SVN更新/检出，实时输出信息到前端
    :param executor: ExecutorScript实例（用于获取output_queue）
    :param svn_logger: 日志实例
    :return: 成功返回True，失败返回错误信息
    """
    from apps.config import bash_script_dir, month_list
    from apps.models.executor_cmd import BatchCommandExecutor

    # svn信息
    svn_dir = SVN_CONFIG['svn_dir']
    svn_com = SVN_CONFIG['svn_com']
    svn_url = SVN_CONFIG['svn_url']

    # 初始化执行器
    cmd_executor = BatchCommandExecutor(
        output_queue=executor.output_queue,
        logger=svn_logger,
        default_timeout=300
    )

    # 1. 确保目录存在
    cmd = f'[[ -d {svn_dir} ]] || mkdir -p {svn_dir}'
    result, success = execute_command(
        cmd_executor=cmd_executor,
        cmd=cmd,
        logger=svn_logger,
        output_queue=executor.output_queue,
        error_msg_prefix="创建目录失败"
    )
    if not success:
        return result

    # 2. 执行SVN更新或检出
    svn_warehouse = os.path.join(svn_dir, '.svn')
    if os.path.exists(svn_warehouse):
        msg = "正在更新SVN资源，请等待..."
        svn_logger.info(msg)
        executor.output_queue.put({"status": "info", "message": msg})
        cmd = f'{svn_com} cleanup {svn_dir} &> /dev/null && {svn_com} up {svn_dir}'
        result, success = execute_command(
            cmd_executor=cmd_executor,
            cmd=cmd,
            logger=svn_logger,
            output_queue=executor.output_queue,
            error_msg_prefix="SVN更新失败"
        )
        if not success:
            return result
        # 记录更新完成日志
        finish_msg = "SVN资源更新完成"
        svn_logger.info(finish_msg)
        executor.output_queue.put({"status": "info", "message": finish_msg})
    else:
        msg = "正在检出SVN资源到，请等待..."
        svn_logger.info(msg)
        executor.output_queue.put({"status": "info", "message": msg})
        cmd = f'{svn_com} co {svn_url} {svn_dir} &> /dev/null'
        result, success = execute_command(
            cmd_executor=cmd_executor,
            cmd=cmd,
            logger=svn_logger,
            output_queue=executor.output_queue,
            error_msg_prefix="SVN检出失败"
        )
        if not success:
            return result
        executor.output_queue.put({"status": "info", "message": "SVN资源检出完成"})

    # 3. 获取当前SVN版本号
    os.chdir(svn_dir)
    cmd = f'{svn_com} info | grep "Last Changed Rev" | grep -o "[0-9]*"'
    result, success = execute_command(
        cmd_executor=cmd_executor,
        cmd=cmd,
        logger=svn_logger,
        output_queue=executor.output_queue,
        error_msg_prefix="获取SVN版本号失败"
    )
    if not success:
        return result
    current_svn_version = result["stdout"]  # 成功时result为status_info
    os.chdir(bash_script_dir)

    # 获取游戏列表
    try:
        game_list_str = GameDBUtil.query_game_list()
        game_list = ast.literal_eval(game_list_str)
    except Exception as e:
        error_msg = f"获取游戏列表异常: {str(e)}"
        svn_logger.error(error_msg)
        return error_msg

    # 筛选重复的
    package_list = set()
    # 4. 只打印要操作的游戏服渠道的代码包文件的时间信息
    package_mode = ['update', 'reload', 'battle']
    for channel in game_list:
        for rsync_mode in package_mode:
            package_list.add(channel_svn_bin(channel, rsync_mode))
    for package_file in package_list:
            cmd = "ls -l %s | awk '{print $6, $7, $8}'" % package_file

            result, success = execute_command(
                cmd_executor=cmd_executor,
                cmd=cmd,
                logger=svn_logger,
                output_queue=executor.output_queue,
                error_msg_prefix="获取包体信息失败"
            )
            if not success:
                return result
            time_parts = result["stdout"].strip().split()
            if len(time_parts) >= 3:
                month_info, day_info, time_info = time_parts[:3]
                month = month_list.get(month_info, month_info)
                executor.output_queue.put({
                    "status": "info",
                    "message": f"包体({package_file})创建时间: {month}月 {day_info}日 {time_info}"
                })

    # 5. 输出SVN版本
    executor.output_queue.put({
        "status": "info",
        "message": f"包体SVN版本号: {current_svn_version}"
    })

    return True