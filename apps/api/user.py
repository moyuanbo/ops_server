#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pytz
from flask import Blueprint, jsonify, request
from flask_login import login_required
from datetime import datetime, timezone
from apps.utils.db_utils import get_connection_pool_status, test_database_connection

from apps.extensions import db
from apps.models.user import UserManager
from apps.models.decorators import admin_required
from apps.config import ZONE_TIME

api = Blueprint('api', __name__)

# 设置时区
zone_time = pytz.timezone(ZONE_TIME)
# 获取当前时间（无时区信息）
current_time = datetime.now()
# 转换为时区格式的时间
zone_current_time = current_time.replace(tzinfo=zone_time)


@api.route('/system/db/status', methods=['GET'])
@login_required
@admin_required
def get_db_status():
    """获取数据库连接池状态"""
    status = get_connection_pool_status()
    connection_ok = test_database_connection()

    return api_response(
        data={
            'connection_pool': status,
            'connection_ok': connection_ok,
            'database_url': db.engine.url.drivername + '://' + db.engine.url.host
        }
    )

# API通用响应格式
def api_response(success=True, data=None, message=None, status_code=200):
    response = {
        'success': success,
        'timestamp': zone_current_time.isoformat()
    }
    if data is not None:
        response['data'] = data
    if message is not None:
        response['message'] = message
    return jsonify(response), status_code


@api.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    """获取用户列表API"""
    users = UserManager.query.all()
    user_list = [{
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'email': user.email,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    } for user in users]
    return api_response(data={'users': user_list})


@api.route('/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    """获取单个用户信息API"""
    user = UserManager.query.get_or_404(user_id)
    user_data = {
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'email': user.email,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    }
    return api_response(data={'user': user_data})


@api.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user_api():
    """创建用户API"""
    data = request.get_json()

    # 验证必填字段
    required_fields = ['username', 'real_name', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return api_response(
                success=False,
                message=f'缺少必填字段: {field}',
                status_code=400
            )

    # 检查用户名和邮箱是否已存在
    if UserManager.query.filter_by(username=data['username']).first():
        return api_response(
            success=False,
            message='用户名已存在',
            status_code=400
        )

    if UserManager.query.filter_by(email=data['email']).first():
        return api_response(
            success=False,
            message='邮箱已被注册',
            status_code=400
        )

    # 创建新用户
    try:
        new_user = UserManager(
            username=data['username'],
            real_name=data['real_name'],
            email=data['email'],
            is_admin=data.get('is_admin', False)
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()

        return api_response(
            data={'user_id': new_user.id},
            message='用户创建成功'
        )
    except Exception as e:
        db.session.rollback()
        return api_response(
            success=False,
            message=f'创建用户失败: {str(e)}',
            status_code=500
        )
