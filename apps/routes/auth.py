#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pytz
# 从 urllib.parse 导入 urlparse
from urllib.parse import urlparse
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    unset_jwt_cookies
)

from apps.extensions import db, limiter, jwt, csrf
from apps.models.user import UserManager
from apps.models.forms import LoginForm
from apps.config import ZONE_TIME

auth = Blueprint('auth', __name__)

# 设置时区
zone_time = pytz.timezone(ZONE_TIME)

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@csrf.exempt  # 表单登录页面豁免CSRF（AJAX登录需注释此行并校验CSRF）
def login():
    # 实例化 LoginForm
    form = LoginForm()

    # 使用表单的 validate_on_submit() 方法
    if form.validate_on_submit():
        # 从表单对象中获取数据
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = UserManager.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('用户名或密码错误')
            # 验证失败时，重定向回登录页
            return redirect(url_for('auth.login'))

        # 2. 生成JWT Token（核心）
        # 过期时间：记住我则7天，否则1小时
        expires_delta = timedelta(days=7) if remember_me else timedelta(hours=1)
        # 以用户ID为Identity（避免敏感信息，如用户名）
        access_token = create_access_token(identity=user.id, expires_delta=expires_delta)

        # 3. 计算跳转页面
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('admin.dashboard' if user.is_admin else 'admin.user_profile')

        # 4. 更新最后登录时间
        current_time = datetime.now().replace(tzinfo=zone_time)
        user.last_login = current_time
        db.session.commit()

        # 5. 封装响应：JWT存入Cookie（防XSS）+ 跳转
        response = make_response(redirect(next_page))
        # ========== 将float转为int ==========
        max_age_seconds = int(expires_delta.total_seconds())
        # 设置JWT到HttpOnly Cookie（禁止JS访问，防XSS）
        response.set_cookie(
            key='access_token_cookie',
            value=access_token,
            httponly=True,  # 核心：防XSS
            secure=True,  # 生产环境开启（仅HTTPS）
            samesite='Lax',  # 核心：防CSRF
            max_age=max_age_seconds
        )
        return response

    # 9. GET 请求时，渲染模板并传入表单对象
    return render_template('auth/login.html', title='登录', form=form)


# ========== 登出接口：清除JWT + JWT认证 ==========
@auth.route('/logout')
@jwt_required()  # 替换原login_required，要求JWT认证
def logout():
    # 清除JWT Cookie
    response = make_response(redirect(url_for('auth.login')))
    unset_jwt_cookies(response)  # 清空access_token_cookie
    return response

# ========== 示例：受JWT+CSRF保护的API接口 ==========
@auth.route('/api/user/info', methods=['GET'])
@jwt_required()  # JWT认证
def get_user_info():
    # 获取JWT中的用户ID
    user_id = get_jwt_identity()
    user = UserManager.query.get(user_id)
    if not user:
        return {'error': '用户不存在'}, 404
    return {
        'id': user.id,
        'username': user.username,
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S')
    }

# ========== JWT错误处理（可选） ==========
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {'error': 'Token已过期'}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {'error': '无效的Token'}, 401
