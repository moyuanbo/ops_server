#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from functools import wraps
from flask import abort, current_app, request, jsonify, redirect, url_for, flash
from flask_login import current_user

def api_csrf_protect(f):
    """API请求的CSRF保护装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查CSRF令牌
        csrf_token = request.headers.get('X-CSRFToken') or request.args.get('csrf_token')
        if not csrf_token or not current_app.extensions['csrf'].validate_csrf(csrf_token):
            current_app.logger.warning(f"API CSRF验证失败: {request.path}")
            return jsonify({
                'success': False,
                'message': 'CSRF验证失败，请刷新页面重试'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    自定义装饰器，用于限制只有管理员才能访问视图函数。

    使用方法：
    @apps.route('/admin/dashboard')
    @login_required  # 通常与 login_required 一起使用，确保用户已登录
    @admin_required
    def admin_dashboard():
        # 管理员才能执行的代码
        pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))

        if not current_user.is_admin:
            flash('您没有管理员权限访问此页面', 'danger')
            abort(403)

        return f(*args, **kwargs)

    return decorated_function
