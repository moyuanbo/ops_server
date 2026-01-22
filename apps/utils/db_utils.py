#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from apps.extensions import db
from apps.models.logger_manager import LoggerManager

logger = LoggerManager()


def get_connection_pool_status():
    """获取连接池状态信息"""
    try:
        engine = db.engine
        pool = engine.pool

        status = {
            'pool_size': pool.size(),
            'checked_in': pool.checkedin(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'max_overflow': pool._max_overflow,
            'recycle': pool._recycle,
            'timeout': pool._timeout
        }

        logger.info(f"连接池状态: {status}")
        return status
    except Exception as e:
        logger.error(f"获取连接池状态失败: {str(e)}")
        return None


def test_database_connection():
    """测试数据库连接"""
    try:
        # 使用连接池预检查机制
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False


def reset_connection_pool():
    """重置连接池（用于维护）"""
    try:
        db.engine.dispose()
        logger.info("连接池已重置")
        return True
    except Exception as e:
        logger.error(f"重置连接池失败: {str(e)}")
        return False
