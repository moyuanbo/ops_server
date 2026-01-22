#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pytz
import traceback
from flask import Blueprint, render_template, request
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from apps.models.logger_manager import LoggerManager
from apps.config import ZONE_TIME

errors = Blueprint('errors', __name__)
logger = LoggerManager()

# 设置时区
zone_time = pytz.timezone(ZONE_TIME)
# 获取当前时间（无时区信息）
current_time = datetime.now()
# 转换为时区格式的时间
zone_current_time = current_time.replace(tzinfo=zone_time)

@errors.app_errorhandler(404)
def error_404(error):
    # 记录404错误日志，便于排查无效访问
    logger.warning(f"404错误：访问不存在的页面 - {request.path} ; 错误信息: {error}")
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(403)
def error_403(error):
    # 记录403错误日志，便于排查无效访问
    logger.warning(f"403错误：访问不存在的页面 - {request.path} ; 错误信息: {error}")
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(500)
def error_500(error):
    # 记录500错误日志，便于排查无效访问
    logger.warning(f"500错误：访问不存在的页面 - {request.path} ; 错误信息: {error}")
    return render_template('errors/500.html'), 500

@errors.app_errorhandler(SQLAlchemyError)
def handle_sql_error(e):
    """处理数据库错误"""
    error_info = {
        'error_message': '数据库操作失败，请稍后重试',
        'error_type': type(e).__name__,
        'error_details': str(e),
        'error_traceback': traceback.format_exc(),
        'error_time': zone_current_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'now': zone_current_time
    }

    # 记录错误日志
    logger.error(f"数据库错误: {str(e)}\n{traceback.format_exc()}")
    return render_template('errors/db_error.html', **error_info), 500