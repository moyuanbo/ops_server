#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from apps.models.logger_manager import LoggerManager
from apps.ops_game.db_utils import GameDBUtil


class AddGameApp:
    def __init__(self, channel_name, game_type, max_game, init_number):
        self.logger = LoggerManager()
        self.channel_name = channel_name
        self.game_type = game_type
        self.max_game = max_game
        self.init_number = int(init_number)
        # 区服类型目录结果配置
        self.game_type_list = {'Global': 'global', 'game_prefix': 'sh_', 'Central': 'central', 'Play': 'play'}


    def add_game_info(self):
        # 参数验证
        if not all([self.channel_name, self.game_type, self.init_number]):
            return 'error', '渠道、区服类型和添加数量为必填项'
        try:
            init_number = int(self.init_number)
            if init_number <= 0:
                raise ValueError
        except ValueError:
            return 'error', '添加数量必须为正整数'

        # 当没有区服信息时，则从0开始
        if self.max_game is None:
            self.max_game = 0

        try:
            self.max_game = int(self.max_game)
            if self.max_game < 0:
                raise ValueError
        except ValueError:
            return 'error', '获取不到最大区服'

        # 生成要装服的操作列表
        filter_list = {self.channel_name: {self.game_type: [self.max_game + i for i in range(1, self.init_number + 1)]}}

        # 先获取服务器列表，后续用于Game部署
        server_list_info = GameDBUtil.get_server_list(self.channel_name, server_type='Game')
        if len(server_list_info) < 0 and self.game_type == 'Game':
            return 'error', f'该渠道({self.channel_name})下的区服类型({self.game_type})没有服务器'

        n = 1
        while init_number >= n:
            # 区服编号（当前要部署的第n个，总编号为max_game + n）
            game_nu = self.max_game + n
            game_info = {'channel': self.channel_name, 'game_type': self.game_type, 'game_nu': game_nu}

            if self.game_type != 'Game':
                # 处理Global/Central类型（最多部署1个）
                if self.game_type == 'Global' or self.game_type == 'Central':
                    if init_number > 1 or (self.max_game + init_number) > 1:
                        return 'error', f'{self.game_type}区服类型 目前最大只能部署一个区服'

                    game_info['game_dir'] = f"{self.game_type_list['game_prefix']}{self.game_type_list[self.game_type]}"
                    game_info['http_port_field'] = f'{self.game_type_list[self.game_type]}_http_port'
                    game_info['db_name'] = f"{self.channel_name}_{self.game_type_list['game_prefix']}{self.game_type_list[self.game_type]}"

                if self.game_type == 'Play':
                    # 验证：最多只能部署2个，且总数量不超过2
                    if init_number > 2 or (self.max_game + init_number) > 2:
                        return 'error', f'{self.game_type}区服类型 目前最大只能部署两个区服'

                    game_info['game_dir'] = f"{self.game_type_list['game_prefix']}{self.game_type_list[self.game_type]}{game_nu}"
                    game_info['http_port_field'] = f'{self.game_type_list[self.game_type]}_init_http_port'
                    game_info['db_name'] = f"{self.channel_name}_{self.game_type_list['game_prefix']}{self.game_type_list[self.game_type]}{game_nu}"

                # 确认服务器
                server_list = GameDBUtil.get_server_list(self.channel_name, other_type=self.game_type)
                if not server_list:
                    return 'error', f'该渠道({self.channel_name})下的区服类型({self.game_type})没有服务器'
                elif len(server_list) > 1:
                    return 'error', f'该渠道({self.channel_name})下的区服类型({self.game_type})配置的服务器过多，请留意'

                # 部署当前区服（第n个）
                add_status = add_game_operation(game_info, server_list[0])
                if add_status != 'success':
                    return 'error', add_status

                # 记录日志部署信息
                self.logger.info(f'该渠道({self.channel_name})下的区服类型({self.game_type})已部署第{n}个区服')

            else:
                game_info['game_dir'] = f"{self.game_type_list['game_prefix']}{game_nu}"
                game_info['db_name'] = f"{self.channel_name}_{self.game_type_list['game_prefix']}{game_nu}"

                # 赋值到另一个变量里，装一个服去除一台服务器
                # 初始化服务器列表（仅首次获取，后续使用剩余列表）
                if not server_list_info:  # 若服务器列表为空，首次获取
                    server_list_info = GameDBUtil.get_server_list(self.channel_name, server_type='Game')
                # 当前可用服务器列表
                server_list = server_list_info

                # 防死循环锁和部署成功标记
                while_lock = 0
                game_deployed = False  # 标记当前区服是否部署成功
                # 循环查找合适的服务器
                while server_list and while_lock < 5:
                    while_lock += 1
                    # 服务器列表索引计数器
                    list_filter = 0
                    # 遍历可用服务器
                    for server_item in server_list:
                        # 检查是否跟上一个区服同一台机器上
                        server_intranet_ip = server_item['intranet_ip']
                        # 获取上一个区服的服务器IP（当前要部署的是第n个，上一个是max_game + n - 1）
                        the_previous_one = self.max_game + n - 1
                        # 首次部署（n=1）时上一个区服可能不存在，需要处理空情况
                        prev_game_info = GameDBUtil.get_game_server_info(self.channel_name, self.game_type,
                                                                         the_previous_one)
                        if not prev_game_info:  # 上一个区服不存在（首次部署），直接使用当前服务器
                            # 部署当前区服
                            add_status = add_game_operation(game_info, server_item)
                            # 从可用列表中移除已使用的服务器
                            del server_list_info[list_filter]
                            if add_status != 'success':
                                return 'error', add_status
                            game_deployed = True  # 标记部署成功
                            break
                        else:
                            # 上一个区服存在，检查是否同IP
                            prev_intranet_ip = prev_game_info[0]['intranet_ip']
                            if server_intranet_ip != prev_intranet_ip:
                                # 不同IP，可部署
                                add_status = add_game_operation(game_info, server_item)
                                del server_list_info[list_filter]  # 移除已用服务器
                                if add_status != 'success':
                                    return 'error', add_status
                                game_deployed = True
                                break

                        # 未找到合适服务器，移动到下一个索引
                        list_filter += 1

                    # 部署成功，退出服务器查找循环
                    if game_deployed:
                        break

                # 检查当前区服是否部署成功
                if not game_deployed:
                    return 'error', f"部署第{n}个区服时未找到合适的服务器（已尝试{while_lock}次）"

            # 检查是否完成所有请求数量的部署
            if n >= init_number:
                message = f'该渠道({self.channel_name})下的区服类型({self.game_type})部署了{n}个区服完成'
                self.logger.info(message)
                write_status = GameDBUtil.write_operation_game_list(filter_list)
                if write_status == 0:
                    return 'error', '列表信息写入到操作列表中失败'
                return 'success', message
            n += 1

        return 'error', '错误信息'

def add_game_operation(game_info, server_list):
    external_ip = server_list['external_ip']
    intranet_ip = server_list['intranet_ip']
    channel_name = game_info['channel']
    game_type = game_info['game_type']
    mysql_ip = GameDBUtil.get_mysql_list(channel_name)
    if mysql_ip is None:
        return f"该渠道({game_info['channel']})下没有MySQL"

    if game_info['game_type'] == 'Play':
        init_http_port = GameDBUtil.get_http_port(channel_name, game_info['http_port_field'])
        http_port = init_http_port + game_info['game_nu']
    elif game_info['game_type'] == 'Global' or game_info['game_type'] == 'Central':
        http_port = GameDBUtil.get_http_port(channel_name, game_info['http_port_field'])
    else:
        http_port = 0

    game_info = (channel_name, game_type, game_info['game_dir'], game_info['game_nu'],
                 external_ip, intranet_ip, mysql_ip, game_info['db_name'], 3, http_port)

    insert_status = GameDBUtil.insert_game_info(game_info)
    if insert_status <= 0:
        return f'该渠道({channel_name})下的区服类型({game_type})写入数据到数据库写入失败'

    return 'success'
