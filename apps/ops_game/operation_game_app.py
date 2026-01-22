#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import ast
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from apps.models.execution_stats import stats_manager
from apps.models.logger_manager import LoggerManager
from apps.models.executor_shell import ExecutorScript
from apps.models.query_channel_svn_bin import channel_svn_bin
from apps.ops_game.svn_operation import svn_update
from apps.ops_game.filter_game_list import format_game_nu
from apps.config import OPERATION_PARAMETER, EXECUTOR_SCRIPTS, MAX_WORKERS

# 导入工具类
from apps.ops_game.db_utils import GameDBUtil
from apps.ops_game.http_utils import HttpUtil
from apps.ops_game.task_utils import TaskUtil


class OperationGameApp:
    def __init__(self):
        self.logger = LoggerManager()
        self.executor = ExecutorScript()  # 脚本执行器（含线程安全队列）
        self.all_futures = []  # 汇总所有任务的futures
        self.task_pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)  # 线程池

    # ------------------------------ 任务提交与生命周期管理 ------------------------------
    def _submit_tasks(self, tasks):
        """提交任务到线程池，返回futures列表"""
        if not tasks:
            self.logger.info("没有需要执行的任务")
            return []

        futures = [
            self.task_pool.submit(
                self.executor.executor_shell,
                logger=self.logger,
                script=task[1],
                parameter=task[2],
                info=task[3],
                executor_scripts=EXECUTOR_SCRIPTS,
                task_id=task[0]
            ) for task in tasks
        ]

        # 后台线程：等待任务完成后清理
        threading.Thread(
            target=self._wait_and_cleanup,
            args=(futures,),
            daemon=True
        ).start()
        return futures

    def _wait_and_cleanup(self, futures_list):
        """等待任务完成并处理异常"""
        for future in as_completed(futures_list):
            if future.exception():
                self.logger.error(f"任务执行异常: {future.exception()}")

    def wait_all_tasks_completion(self):
        """等待所有任务完成并发送统计和终止信号"""
        for _ in as_completed(self.all_futures):
            pass  # 仅等待

        # 推送统计和完成信号
        stats_data = stats_manager.get_stats()
        self.executor.output_queue.put({
            "status": "statistics",
            "message": "执行统计结果",
            "data": stats_data
        })
        self.executor.output_queue.put({
            "status": "completed",
            "message": "所有任务执行完毕"
        })
        self.executor.output_queue.put(None)  # 终止信号
        self.task_pool.shutdown(wait=True)

    # ------------------------------ 操作类型处理 ------------------------------
    def _handle_stop_start(self, script, tasks):
        """处理启动/停止操作（按顺序执行）"""
        operation_order = ['Central', 'Play', 'Global', 'Game'] if script == 'stop_game' \
            else ['Central', 'Game', 'Play', 'Global']

        # 按服务类型分组
        task_groups = defaultdict(list)
        for task in tasks:
            task_groups[task[4]].append(task)  # task[4]是game_type

        def process_groups():
            try:
                for type_name in operation_order:
                    group_tasks = task_groups.get(type_name, [])
                    if not group_tasks:
                        self.logger.info(f"无{type_name}类型服务需要处理，跳过...")
                        continue

                    self.logger.info(f"开始处理{type_name}类型服务，共{len(group_tasks)}个任务")
                    group_futures = self._submit_tasks(group_tasks)
                    self.all_futures.extend(group_futures)

                    # 等待当前组所有任务完成
                    for future in as_completed(group_futures):
                        if future.exception():
                            self.logger.error(f"{type_name}类型服务处理异常: {future.exception()}")
                    self.logger.info(f"{type_name}类型服务已全部处理完成")
                    time.sleep(5)  # 预留服务状态切换时间

                self.logger.info("所有类型服务处理完成")
            except Exception as e:
                self.logger.error(f"处理服务组时发生异常: {str(e)}")
            finally:
                # 所有组处理完成后关闭线程池
                self.task_pool.shutdown(wait=True)
                self.wait_all_tasks_completion()

        threading.Thread(target=process_groups, daemon=True).start()

    def _handle_reload(self, main_futures, reload_list_tasks, reload_status_task):
        """处理热更操作（基础任务+HTTP请求）"""
        def process_reload():
            # 等待基础任务完成
            for future in as_completed(main_futures):
                if future.exception():
                    self.logger.error(f"基础任务执行异常: {future.exception()}")

            # 等待代码同步到区服里
            time.sleep(1)
            # 执行热更请求
            self.logger.info("开始执行热更接口请求...")
            for url in reload_list_tasks:
                HttpUtil.request_with_log(url, self.logger, self.executor.output_queue, "热更请求")

            # 等待热更请求完成
            time.sleep(5)
            # 检查热更状态
            self.logger.info("开始检查热更状态...")
            for url in reload_status_task:
                HttpUtil.request_with_log(url, self.logger, self.executor.output_queue, "热更状态检查")

            self.logger.info("热更操作全流程完成")
            self.executor.output_queue.put({
                "status": "completed",
                "message": "热更操作全流程完成"
            })

        reload_future = self.task_pool.submit(process_reload)
        self.all_futures.append(reload_future)

    def _handle_rsync(self, unique_ips, rsync_mode):
        """处理同步代码到服务器操作"""
        # 原SVN更新逻辑
        svn_result = svn_update(self.logger, self.executor)
        if svn_result is not True:
            # 此处去掉yield，改为返回错误信息字符串
            return f"SVN更新失败: {svn_result}"

        tasks = []
        for game_ip_str in unique_ips:
            game_ip, channel = game_ip_str.split("__")
            package_file = channel_svn_bin(channel, rsync_mode)

            task_id = f"RSYNC_{channel}_{game_ip}"
            info = f"服务器({game_ip})同步代码包"
            parameter = f"{channel} {game_ip} rsync {package_file}"
            tasks.append((task_id, 'rsync_game', parameter, info, "RSYNC"))
        return tasks

    # ------------------------------ 主流程 ------------------------------
    def operation_game(self, script='status_game', rsync_mode=None):
        """主操作入口"""
        stats_manager.reset()
        self.all_futures = []
        operation = script.split('_')[0]
        # svn锁
        svn_lock = 'lock'
        lock_status = 0

        # 校验操作参数
        if operation not in OPERATION_PARAMETER:
            error_msg = f"未找到操作参数: {script}"
            self.logger.error(error_msg)
            yield f"data: {{\"status\": \"error\", \"message\": \"{error_msg}\"}}\n\n"
            return

        # 获取游戏列表
        try:
            game_list_str = GameDBUtil.query_game_list()
            game_list = ast.literal_eval(game_list_str)
        except Exception as e:
            error_msg = f"获取游戏列表异常: {str(e)}"
            self.logger.error(error_msg)
            yield f"data: {{\"status\": \"error\", \"message\": \"{error_msg}\"}}\n\n"
            return

        # 初始化任务相关变量
        tasks = []
        reload_list_tasks = set()
        reload_status_task = set()
        unique_ips = set()
        operation_desc = OPERATION_PARAMETER[operation]

        # 生成基础任务
        for channel in game_list:
            external_switch = GameDBUtil.get_external_switch(channel)
            for game_type in game_list[channel]:
                # 处理热更相关任务（Central类型）
                if script == 'reload_game' or rsync_mode == 'reload':
                    if game_type == 'Game':
                        central_servers = GameDBUtil.get_central_server_info(channel, external_switch)
                        for server in central_servers:
                            game_ip = server['intranet_ip'] if int(external_switch) != 1 else server['external_ip']
                            game_dir = server['server_dir']
                            http_port = server['http_port']

                            # 生成Central基础任务
                            if 'Central' not in game_list[channel]:
                                task_id = TaskUtil.generate_task_id(channel, 'Central', 1)
                                info = TaskUtil.generate_task_info(channel, 'Central', 1, game_ip, operation_desc)
                                parameter = f"{channel} {game_ip} {game_dir} {operation}"
                                tasks.append((task_id, script, parameter, info, game_type))

                            # 获取渠道的游戏服初始zone_id
                            zone_id = int(GameDBUtil.get_channel_initial_id(channel))
                            # 收集热更URL
                            reload_url = GameDBUtil.get_reload_url('Game')
                            reload_list = format_game_nu(game_list[channel][game_type], zone_id)
                            reload_list_tasks.add(f'http://{game_ip}:{http_port}{reload_url}{reload_list}')

                            status_url = GameDBUtil.get_reload_url('status')
                            reload_status_task.add(f'http://{game_ip}:{http_port}{status_url}')

                            unique_ips.add(f"{game_ip}__{channel}")

                # 处理录像更新
                elif script == 'battle_game' or rsync_mode == 'battle':
                    if game_type != 'Game':
                        continue

                # 处理普通游戏服任务
                for game in game_list[channel][game_type]:
                    try:
                        game_info = GameDBUtil.get_game_server_info(channel, game_type, game)
                        if not game_info:
                            error_msg = f"未找到游戏信息: 渠道={channel}, 类型={game_type}, 区服={game}"
                            self.logger.error(error_msg)
                            yield f"data: {{\"status\": \"warning\", \"message\": \"{error_msg}\"}}\n\n"
                            continue

                        # 处理IP和目录信息
                        game_dir = game_info[0]['server_dir']
                        intranet_ip = game_info[0]['intranet_ip']
                        game_ip = intranet_ip

                        if int(external_switch) == 1:
                            external_ip = GameDBUtil.get_external_ip(intranet_ip)
                            if not external_ip:
                                error_msg = f"未找到服务器信息: 内网IP={intranet_ip}"
                                self.logger.error(error_msg)
                                yield f"data: {{\"status\": \"warning\", \"message\": \"{error_msg}\"}}\n\n"
                                continue
                            game_ip = external_ip

                        # 热更操作特殊处理（非Game类型）
                        if script == 'reload_game' and game_type != 'Game':
                            game_info = GameDBUtil.get_central_server_info(channel, external_switch, game_type, game)
                            for server in game_info:
                                reload_url = GameDBUtil.get_reload_url('other')
                                reload_list_tasks.add(f'http://{game_ip}:{server["http_port"]}{reload_url}')

                        # 收集IP和生成任务，只对同步代码到服务器调用
                        unique_ips.add(f"{game_ip}__{channel}")

                        # 收集游戏服信息
                        task_id = TaskUtil.generate_task_id(channel, game_type, game)
                        info = TaskUtil.generate_task_info(channel, game_type, game, game_ip, operation_desc)
                        if script == 'initial_game':
                            # 当第一个区服才不加锁
                            if svn_lock == 'lock' and lock_status == 0:
                                lock_status += 1
                                svn_lock = 'no_lock'
                            else:
                                svn_lock = 'lock'
                            parameter = f"{channel} {game_ip} {game_type} {game_dir} {game} {svn_lock} {operation}"
                        else:
                            parameter = f"{channel} {game_ip} {game_dir} {operation}"
                        tasks.append((task_id, script, parameter, info, game_type))

                    except Exception as e:
                        error_msg = (f"处理游戏信息异常: 渠道={channel}, 类型={game_type}, "
                                     f"区服={game}, 错误={str(e)}")
                        self.logger.error(error_msg)
                        yield f"data: {{\"status\": \"error\", \"message\": \"{error_msg}\"}}\n\n"
                        continue

        # 处理不同操作类型
        if script == 'rsync_game':
            tasks = self._handle_rsync(unique_ips, rsync_mode)
            # 检查是否返回错误信息
            if isinstance(tasks, str):
                yield f"data: {{\"status\": \"error\", \"message\": \"{tasks}\"}}\n\n"
                return

            # 正常处理任务列表
            main_futures = self._submit_tasks(tasks)
            self.all_futures.extend(main_futures)
            threading.Thread(target=self.wait_all_tasks_completion, daemon=False).start()

        elif script in ('stop_game', 'start_game'):
            self._handle_stop_start(script, tasks)

        else:
            main_futures = self._submit_tasks(tasks)
            self.all_futures.extend(main_futures)

            # 处理热更后续任务
            if script == 'reload_game':
                self._handle_reload(main_futures, reload_list_tasks, reload_status_task)

            threading.Thread(target=self.wait_all_tasks_completion, daemon=False).start()

        # 输出流生成器
        yield from self.executor.get_output_generator(self.logger)
