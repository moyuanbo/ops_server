#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import json

from apps.models.operation_mysql import MysqlConfig
from apps.config import MYSQL_CONFIG
from apps.models.logger_manager import LoggerManager

# 数据库连接及配置初始化
db_manager = MysqlConfig()
logger = LoggerManager()

# 表名配置
game_list_table = MYSQL_CONFIG['game_list_table']
server_list_table = MYSQL_CONFIG['server_list']
channel_list = MYSQL_CONFIG['channel_list']
reload_url_list = MYSQL_CONFIG['reload_url_list']
server_list = MYSQL_CONFIG['server_list']
mysql_list = MYSQL_CONFIG['mysql_list']
operation_game_list = MYSQL_CONFIG['operation_game_list']


class GameDBUtil:
    """游戏数据库操作工具类"""
    @staticmethod
    def query_game_list() -> str:
        """查询当前操作游戏列表"""
        sql = f"SELECT operation_game_list FROM {operation_game_list} WHERE id=1;"
        game_list = db_manager.execute_query(sql)
        return game_list[0]['operation_game_list'] if game_list else ""

    @staticmethod
    def get_external_switch(channel):
        """获取渠道的内外网开关状态"""
        sql = f"SELECT `external_switch` FROM `{channel_list}` WHERE `channel_name` = %s"
        result = db_manager.execute_query(sql, (channel,))
        return result[0]['external_switch'] if result else 0

    @staticmethod
    def get_channel_initial_id(channel):
        """获取渠道的游戏服初始zone_id"""
        sql = f"SELECT `initial_id` FROM `{channel_list}` WHERE `channel_name` = %s"
        result = db_manager.execute_query(sql, (channel,))
        return result[0]['initial_id']

    @staticmethod
    def get_central_server_info(channel, external_switch, game_type='Central', game_num=1):
        """获取中心服信息（用于热更）"""
        if int(external_switch) == 1:
            sql = (f'SELECT external_ip, server_dir, http_port FROM {game_list_table} WHERE '
                   f'channel_name = %s AND server_type = %s AND game_nu = %s')
        else:
            sql = (f'SELECT intranet_ip, server_dir, http_port FROM {game_list_table} WHERE '
                   f'channel_name = %s AND server_type = %s AND game_nu = %s')
        return db_manager.execute_query(sql, (channel, game_type, game_num))

    @staticmethod
    def get_game_server_info(channel, game_type, game_nu):
        """获取游戏服基础信息"""
        sql = (f"SELECT server_dir, intranet_ip FROM {game_list_table} "
               f"WHERE channel_name='{channel}' AND server_type='{game_type}' AND game_nu={game_nu}")
        return db_manager.execute_query(sql)

    @staticmethod
    def get_external_ip(intranet_ip):
        """通过内网IP查询外网IP"""
        sql = f"SELECT external_ip FROM {server_list_table} WHERE intranet_ip='{intranet_ip}'"
        result = db_manager.execute_query(sql)
        return result[0]['external_ip'] if result else None

    @staticmethod
    def get_reload_url(reload_type):
        """获取热更相关URL"""
        sql = f'SELECT reload_url FROM {reload_url_list} WHERE reload_type=%s'
        result = db_manager.execute_query(sql, (reload_type,))
        return result[0]['reload_url'] if result else ''

    @staticmethod
    def get_server_list(channel, server_type=None, other_type=None):
        """获取服务器列表"""
        if server_type:
            sql = f'SELECT `external_ip`, `intranet_ip` FROM `{server_list}` WHERE `belong_to_channel`="{channel}" AND server_type="{server_type}"'
        elif other_type:
            sql = f'SELECT `external_ip`, `intranet_ip` FROM `{server_list}` WHERE `belong_to_channel`="{channel}" AND `{other_type}_server_type`=0'
        else:
            return None

        result = db_manager.execute_query(sql)
        return result if result else ''

    @staticmethod
    def get_mysql_list(channel):
        """获取MySQL列表"""
        sql = f'SELECT intranet_ip FROM {mysql_list} WHERE belong_to_channel=%s ORDER BY id DESC LIMIT 1'
        result = db_manager.execute_query(sql, (channel,))
        return result[0]['intranet_ip'] if result else None

    @staticmethod
    def get_http_port(channel, field):
        """获取区服http端口列表"""
        sql = f'SELECT {field} FROM {channel_list} WHERE `channel_name`=%s'
        result = db_manager.execute_query(sql, (channel,))
        return result[0][field] if result else None

    @staticmethod
    def insert_game_info(params):
        """写入要装服的信息到运维游戏服列表中"""
        sql = (f"INSERT INTO `{game_list_table}` (`channel_name`, `server_type`, `server_dir`, `game_nu`, "
               f"`external_ip`, `intranet_ip`, `server_db_ip`, `server_db_name`, `game_status`, `http_port`) "
               f"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        result = db_manager.insert_data(sql, params)
        return result

    @staticmethod
    def write_operation_game_list(filter_list):
        """处理查询结果并写入操作游戏列表"""
        try:
            # 清空并写入新数据（使用参数化更新避免SQL语法错误）
            clear_sql = f"UPDATE operation_game_list SET {operation_game_list} = '' WHERE id = 1;"
            db_manager.execute_update(clear_sql)

            # 写入新数据（JSON序列化）
            filter_json = json.dumps(filter_list)
            update_sql = f"UPDATE operation_game_list SET {operation_game_list} = %s WHERE id = 1;"
            status = db_manager.execute_update(update_sql, (filter_json,))

            return filter_list if status == 1 else 0

        except Exception as e:
            logger.error(f"写入操作游戏列表失败：{str(e)}")
            return 0
