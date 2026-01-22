#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from typing import Tuple, List, Dict, Optional

from apps.config import MYSQL_CONFIG
from apps.ops_game.db_utils import GameDBUtil
from apps.models.operation_mysql import MysqlConfig
from apps.models.logger_manager import LoggerManager


def parse_game_nu(game_nu_str: Optional[str], return_full_list: bool = False
                  ) -> Tuple[List[Tuple[int, int]], List[int]] | List[int]:
    """
    解析区服字符串（支持混合格式）
    :param game_nu_str: 区服字符串（如1,3,4_5,7,8_10,20）
    :param return_full_list: 是否返回完整的区服列表
    :return: 若return_full_list=True，返回排序后的完整区服列表；否则返回(ranges, singles)
    """
    ranges = []
    singles = []

    if not game_nu_str:
        return [] if return_full_list else (ranges, singles)

    # 清理输入
    cleaned_str = game_nu_str.strip().strip(',')
    items = [item.strip() for item in cleaned_str.split(',') if item.strip()]

    for item in items:
        if '_' in item:
            try:
                start, end = map(int, item.split('_', 1))
                if start <= end:
                    ranges.append((start, end))
            except (ValueError, IndexError):
                continue
        else:
            try:
                singles.append(int(item))
            except ValueError:
                continue

    # 若需要返回完整列表：合并范围+单个区服并排序
    if return_full_list:
        full_list = singles.copy()
        for start, end in ranges:
            full_list.extend(range(start, end + 1))
        # 去重+升序排序
        return sorted(list(set(full_list)))
    return ranges, singles


def format_game_nu(game_nu_list, initial_id=0):
    """
    将区服列表格式化为紧凑字符串（如[1,2,3,6,9,12,13] → "1_3,6,9,12_13"）
    并为每个区服数字加上渠道初始ID，生成全局唯一的zone_id
    :param game_nu_list: 热更的区服相对编号列表
    :param initial_id: 渠道的游戏服初始id（偏移量）
    :return: 返回热更的游戏服zone_id的格式化紧凑字符串
    """
    if not game_nu_list:
        return ""

    # 排序并去重：先处理原始区服编号
    sorted_nus = sorted(list(set(game_nu_list)))
    # 为每个区服编号加上初始ID，得到全局zone_id
    zone_ids = [nu + initial_id for nu in sorted_nus]

    ranges = []
    # 用加过偏移的zone_id初始化
    current_start = zone_ids[0]
    current_end = zone_ids[0]

    # 遍历加过偏移的zone_id列表，合并连续范围
    for nu in zone_ids[1:]:
        if nu == current_end + 1:
            current_end = nu
        else:
            # 结束当前范围
            if current_start == current_end:
                ranges.append(str(current_start))
            else:
                ranges.append(f"{current_start}_{current_end}")
            current_start = nu
            current_end = nu

    # 处理最后一个范围
    if current_start == current_end:
        ranges.append(str(current_start))
    else:
        ranges.append(f"{current_start}_{current_end}")

    return ",".join(ranges)


class GameListFilter:
    def __init__(self):
        self.logger = LoggerManager()
        self.db_manager = MysqlConfig()
        self.db_manager.connect_pool()
        self.game_list_table = MYSQL_CONFIG['game_list_table']
        self.channel_list = MYSQL_CONFIG['channel_list']
        self.game_type_list = MYSQL_CONFIG['game_type_list']

    # 把查询到的 要操作游戏服列表 写入到数据库中
    def write_operation_game_list(self, sql, params=None):
        """
        处理查询结果并写入操作游戏列表
        :param sql: 查询SQL语句
        :param params: SQL参数（用于参数化查询）
        :return: 处理后的游戏列表或0（失败时）
        """
        # 执行参数化查询（params为None时兼容原逻辑）
        game_data = self.db_manager.execute_query(sql, params) if params else self.db_manager.execute_query(sql)
        filter_list = {}
        for game in game_data:
            channel_name = game['channel_name']
            server_type = game['server_type']
            game_nu = game['game_nu']
            # 构建过滤后的游戏列表（使用setdefault方法）
            filter_list.setdefault(channel_name, {}).setdefault(server_type, []).append(game_nu)

        return GameDBUtil.write_operation_game_list(filter_list)

    def _build_game_query_sql(self,
                              channel_name: Optional[list | str] = None,
                              server_type: Optional[list | str] = None,
                              game_nu: Optional[str] = None,
                              update_mode: Optional[str] = None) -> Tuple[str, Tuple]:
        """内部方法：动态构建游戏查询SQL和参数（新增update_mode参数）"""
        # 初始化查询SQL（热更时排除game_nu=9999）
        base_sql = f'SELECT channel_name, server_type, game_nu FROM {self.game_list_table} WHERE game_status IN (0, 1)'

        # 热更模式：排除game_nu=9999
        if update_mode == 'reload':
            base_sql += " AND game_nu != 9999"

        # 存储所有参数值
        params = []

        # ========== 统一处理渠道参数格式 ==========
        # 兼容：如果是长度为1的列表，转为字符串（单选场景）
        if isinstance(channel_name, list):
            if len(channel_name) == 1:
                channel_name = channel_name[0]  # 单选列表转字符串
            elif len(channel_name) == 0:
                channel_name = None  # 空列表视为"全部"

        # 1. 处理渠道条件（适配多选/全部/单选）
        if channel_name:
            if isinstance(channel_name, list) and len(channel_name) > 0:
                # 多选渠道（列表长度>1）
                placeholders = ', '.join(['%s'] * len(channel_name))
                base_sql += f" AND channel_name IN ({placeholders})"
                params.extend(channel_name)
            elif isinstance(channel_name, str):
                # 单选渠道（字符串/长度为1的列表转换后）
                base_sql += " AND channel_name = %s"
                params.append(channel_name)
        # channel_name为null → 全部渠道（不拼接条件）

        # ========== 处理区服类型条件（适配多选） ==========
        if server_type:
            if isinstance(server_type, list) and len(server_type) > 0:
                # 多选区服类型
                placeholders = ', '.join(['%s'] * len(server_type))
                base_sql += f" AND server_type IN ({placeholders})"
                params.extend(server_type)
            elif isinstance(server_type, str):
                # 单选区服类型
                base_sql += " AND server_type = %s"
                params.append(server_type)

        # 3. 处理区服条件（多范围+单区服混合）
        ranges, singles = parse_game_nu(game_nu)
        # 存储区服相关的SQL条件片段
        game_conditions = []

        # 处理范围条件（BETWEEN）
        for start, end in ranges:
            game_conditions.append("game_nu BETWEEN %s AND %s")
            # 添加范围参数
            params.extend([start, end])

        # 处理单个区服条件（IN）
        if singles:
            placeholders = ', '.join(['%s'] * len(singles))
            game_conditions.append(f"game_nu IN ({placeholders})")
            # 添加单个区服参数
            params.extend(singles)

        # 拼接区服条件（多个条件用OR连接）
        if game_conditions:
            base_sql += " AND (" + " OR ".join(game_conditions) + ")"

        # 排序
        base_sql += ' ORDER BY channel_name, server_type, game_nu;'
        return base_sql, tuple(params)

    def query_game_db(self,
                      channel_name: Optional[str | list] = None,
                      server_type: Optional[str | list] = None,
                      game_nu: Optional[str] = None,
                      update_mode: Optional[str] = None) -> Tuple[List[Dict], Dict or int]:
        """统一查询入口，新增update_mode参数"""
        try:
            sql, params = self._build_game_query_sql(channel_name, server_type, game_nu, update_mode)
            result = self.db_manager.execute_query(sql, params)
            filter_list = self.write_operation_game_list(sql, params) if result else {}
            return result, filter_list
        except Exception as e:
            self.logger.error(f"查询游戏服失败：{str(e)}")
            return [], 0

    def get_distinct_channels(self) -> List[str]:
        """获取游戏服列表下的所有不重复的渠道名称"""
        sql = f'SELECT DISTINCT channel_name FROM {self.game_list_table} ORDER BY channel_name'
        rows = self.db_manager.execute_query(sql)
        return [r['channel_name'] for r in rows]

    def get_distinct_server_type(self, channel_name: str) -> List[str]:
        """获取游戏服列表下的指定渠道下的所有服务器类型"""
        sql = f'SELECT DISTINCT server_type FROM {self.game_list_table} WHERE channel_name = %s ORDER BY server_type'
        rows = self.db_manager.execute_query(sql, (channel_name,))
        return [r['server_type'] for r in rows]

    def get_games(self, channel_name: str, server_type: str) -> List[int]:
        """获取游戏服列表下的指定渠道和类型下的所有游戏服"""
        sql = f'''SELECT game_nu FROM {self.game_list_table} WHERE channel_name = %s AND server_type = %s 
                 ORDER BY game_nu'''
        rows = self.db_manager.execute_query(sql, (channel_name, server_type))
        return [r['game_nu'] for r in rows]

    def get_channel_list(self) -> List[str]:
        """获取渠道列表"""
        sql = f'SELECT channel_name FROM {self.channel_list} ORDER BY channel_name;'
        rows = self.db_manager.execute_query(sql)
        return [r['channel_name'] for r in rows]

    def get_game_type_list(self) -> List[str]:
        """获取渠道列表"""
        sql = f'SELECT server_type FROM {self.game_type_list} ORDER BY server_type;'
        rows = self.db_manager.execute_query(sql)
        return [r['server_type'] for r in rows]

    def get_max_game(self, channel_name: str, server_type: str) -> Optional[int]:
        """获取指定渠道和类型下的最大区服号（无区服时返回None）"""
        sql = f'''SELECT game_nu FROM {self.game_list_table} WHERE channel_name = %s AND server_type = %s 
                 AND game_status != 1 ORDER BY game_nu DESC LIMIT 1'''
        rows = self.db_manager.execute_query(sql, (channel_name, server_type))
        # 有数据则返回最大值，无数据返回None
        return rows[0]['game_nu'] if rows else None
