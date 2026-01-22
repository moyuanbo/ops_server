#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pymysql
from dbutils.pooled_db import PooledDB

from apps.models.logger_manager import LoggerManager
from apps.config import MYSQL_CONFIG

db_user = MYSQL_CONFIG['user']
db_password = MYSQL_CONFIG['passwd']
db_host = MYSQL_CONFIG['host']
db_port = MYSQL_CONFIG['port']
db_name = MYSQL_CONFIG['db_name']


class MysqlConfig:
    def __init__(self, host=db_host, port=db_port, user=db_user, password=db_password, database=db_name, charset='utf8mb4'):
        self.logger = LoggerManager()
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=10,
            mincached=2,
            maxcached=5,
            maxshared=3,
            blocking=True,
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset=charset,
            cursorclass=pymysql.cursors.DictCursor
        )

    def connect_pool(self):
        """获取连接池中的连接"""
        try:
            return self.pool.connection()
        except Exception as e:
            self.logger.error(f"[FAIL]获取数据库连接失败：{e}")
            return None

    def execute_query(self, sql, params=None):
        """
        执行查询操作（参数化SQL）
        :param sql: SQL语句（使用%s作为占位符）
        :param params: SQL参数（元组或字典，None表示无参数）
        :return: 查询结果列表
        """
        conn = self.connect_pool()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                # 执行参数化查询，避免SQL注入
                cursor.execute(sql, params or ())
                result = cursor.fetchall()
                self.logger.info(f"[SUCCESS]查询成功. SQL: {sql}, Params: {params}")
                return result
        except Exception as e:
            self.logger.error(f"[FAIL]查询执行失败：{e}. SQL: {sql}, Params: {params}")
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                # 连接返回连接池，而不是关闭MySQL的连接
                conn.close()

    def execute_update(self, sql, params=None):
        """
        执行增删改操作（参数化SQL）
        :param sql: SQL语句（使用%s作为占位符）
        :param params: SQL参数（元组或字典，None表示无参数）
        :return: 受影响的行数
        """
        conn = self.connect_pool()
        if not conn:
            return 0

        try:
            with conn.cursor() as cursor:
                # 执行参数化更新
                affected_rows = cursor.execute(sql, params or ())
                conn.commit()
                self.logger.info(f"[SUCCESS]更新成功. 受影响行数: {affected_rows}. SQL: {sql}, Params: {params}")
                return affected_rows
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"[FAIL]更新操作失败：{e}. SQL: {sql}, Params: {params}")
            return 0
        finally:
            if 'cursor' in locals():
                cursor.close()
            if conn:
                # 连接返回连接池，而不是关闭MySQL的连接
                conn.close()

    def insert_data(self, sql, params=None):
        """
        插入数据（参数化SQL）
        :param sql: 插入SQL语句
        :param params: 插入参数
        :return: 受影响的行数
        """
        return self.execute_update(sql, params)
