#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import pytz
from flask import jsonify
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from apps.extensions import db
from apps.models.user import UserManager
from apps.models.logger_manager import LoggerManager
from apps.models.forms import UserForm, PasswordChangeForm
from apps.models.decorators import admin_required
from apps.config import ZONE_TIME

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = LoggerManager()

# 设置时区
zone_time = pytz.timezone(ZONE_TIME)

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # 统计数据：总用户数、管理员数、普通用户数
    total_users = UserManager.query.count()
    admin_users = UserManager.query.filter_by(is_admin=True).count()
    normal_users = total_users - admin_users

    # 传递数据到模板
    return render_template(
        'admin/dashboard.html',
        title='控制台',
        total_users=total_users,
        admin_users=admin_users,
        normal_users=normal_users
    )

@admin_bp.route('/')
@admin_bp.route('/index')
@login_required
@admin_required
def index():
    """管理员首页"""
    # 现有统计数据
    user_count = UserManager.query.count()
    admin_count = UserManager.query.filter_by(is_admin=True).count()
    locked_count = UserManager.query.filter_by(account_locked=True).count()

    # 获取当前时间（无时区信息）
    current_time = datetime.now()
    # 转换为时区格式的时间
    zone_current_time = current_time.replace(tzinfo=zone_time)
    # 本周活跃用户（假设用户模型有 last_login 字段记录最后登录时间）
    seven_days_ago = zone_current_time - timedelta(days=7)
    active_users = UserManager.query.filter(
        UserManager.last_login >= seven_days_ago
    ).count()

    return render_template(
        'admin/index.html',
        title='仪表盘',
        user_count=user_count,
        admin_count=admin_count,
        locked_count=locked_count,
        active_users=active_users,
        current_time=zone_current_time
    )


# 用户列表接口（补充：确保user_list路由存在）
@admin_bp.route('/user_list')
@login_required
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # 每页10条
    users = UserManager.query.filter_by(is_deleted=False).paginate(page=page, per_page=per_page)
    return render_template('admin/user_list.html', users=users, title='用户管理')


@admin_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """创建用户，友好处理密码验证"""
    form = UserForm()

    if form.validate_on_submit():
        # 检查用户名和邮箱是否已存在
        if UserManager.query.filter_by(username=form.username.data).first():
            flash('用户名已存在', 'danger')
            return render_template('admin/create_user.html', form=form, title='创建用户')

        if UserManager.query.filter_by(email=form.email.data).first():
            flash('邮箱已被注册', 'danger')
            return render_template('admin/create_user.html', form=form, title='创建用户')

        # 创建新用户
        try:
            new_user = UserManager(
                username=form.username.data,
                real_name=form.real_name.data,
                email=form.email.data,
                is_admin=form.is_admin.data
            )

            # 设置密码（如果提供）
            if form.password.data:
                try:
                    # 调用set_password，若密码无效会抛出ValueError
                    new_user.set_password(form.password.data)
                except ValueError as e:
                    # 捕获密码强度不足地异常，显示错误信息
                    flash(str(e), 'danger')
                    return render_template('admin/create_user.html', form=form, title='创建用户')

            else:
                # 生成随机密码
                from apps.utils.password_utils import generate_strong_password
                random_password = generate_strong_password()
                new_user.set_password(random_password)
                flash(f'用户创建成功，初始密码：{random_password}', 'info')

            db.session.add(new_user)
            db.session.commit()

            flash(f'用户 {form.username.data} 创建成功', 'success')
            return redirect(url_for('admin.user_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'创建用户失败: {str(e)}', 'danger')
            return render_template('admin/create_user.html', form=form, title='创建用户')

    # 表单验证失败时显示错误信息
    return render_template('admin/create_user.html', form=form, title='创建用户')


@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """编辑用户"""
    user = UserManager.query.get_or_404(user_id)
    form = UserForm(obj=user)

    # 不允许编辑自己的管理员权限
    if user.id == current_user.id and not request.form.get('is_admin'):
        flash('不能取消自己的管理员权限', 'warning')
        # 直接渲染模板，保留表单状态，避免重定向循环
        return render_template('admin/edit_user.html', form=form, user=user, title='编辑用户')

    if form.validate_on_submit():
        # 检查用户名是否已存在（排除当前用户）
        existing_user = UserManager.query.filter(
            UserManager.username == form.username.data,
            UserManager.id != user_id
        ).first()
        if existing_user:
            flash('用户名已存在', 'danger')
            return render_template('admin/edit_user.html', form=form, user=user, title='编辑用户')

        # 检查邮箱是否已存在（排除当前用户）
        existing_email = UserManager.query.filter(
            UserManager.email == form.email.data,
            UserManager.id != user_id
        ).first()
        if existing_email:
            flash('邮箱已被注册', 'danger')
            return render_template('admin/edit_user.html', form=form, user=user, title='编辑用户')

        try:
            # 更新用户信息
            user.username = form.username.data
            user.real_name = form.real_name.data
            user.email = form.email.data
            user.is_admin = form.is_admin.data

            # 如果提供了新密码，则更新
            if form.password.data:
                try:
                    user.set_password(form.password.data)  # 可能抛出ValueError
                except ValueError as e:
                    # 捕获密码强度不足的异常，显示具体错误
                    flash(str(e), 'danger')
                    return render_template('admin/edit_user.html', form=form, user=user, title='编辑用户')

            db.session.commit()
            flash(f'用户 {user.username} 更新成功', 'success')
            return redirect(url_for('admin.user_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'更新用户失败: {str(e)}', 'danger')

    # 初始化时清空密码字段
    form.password.data = ''
    form.password2.data = ''

    return render_template('admin/edit_user.html', form=form, user=user, title='编辑用户')


# 删除用户接口
@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    try:
        result = UserManager.delete_user(user_id)
        msg = '删除成功' if result else '用户不存在或已删除'
        return jsonify({'success': result, 'msg': msg})
    except Exception as e:
        # 记录详细错误日志
        logger.error(f"删除用户{user_id}失败: {str(e)}")
        # 返回用户友好的错误信息
        return jsonify({'success': False, 'msg': '删除失败：系统错误'}), 500


@admin_bp.route('/unlock_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def unlock_user(user_id):
    """解锁用户账号"""
    result = UserManager.unlock_user(user_id)
    return jsonify(result)


@admin_bp.route('/lock_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def lock_user(user_id):
    """锁定用户账号"""
    result = UserManager.lock_user(user_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(result)  # 直接返回模型方法的结果字典
    else:
        flash(result['msg'], 'success' if result['success'] else 'danger')
        return redirect(url_for('admin.user_list'))


@admin_bp.route('/user_profile')
@login_required
def user_profile():
    """个人资料"""
    return render_template('admin/user_profile.html', user=current_user)


@admin_bp.route('/profile/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码，友好提示"""
    form = PasswordChangeForm()

    if form.validate_on_submit():
        # 验证原密码
        if not current_user.check_password(form.old_password.data):
            flash('原密码错误', 'danger')
            return render_template('admin/change_password.html', form=form)

        try:
            # 修改密码
            if not current_user.set_password(form.new_password.data):
                flash('密码强度不够，需包含大小写字母、数字和特殊字符，长度至少8位', 'danger')
                return render_template('admin/change_password.html', form=form)

            db.session.commit()
            flash('密码修改成功，请使用新密码登录', 'success')
            return redirect(url_for('auth.logout'))

        except Exception as e:
            db.session.rollback()
            flash(f'修改密码失败: {str(e)}', 'danger')

    return render_template('admin/change_password.html', form=form)


@admin_bp.route('/system_status')
@login_required
@admin_required
def system_status():
    """系统状态页面"""
    return render_template('admin/system_status.html', title='系统状态')
