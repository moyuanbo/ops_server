# app/routes/admin.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps

from app.extensions import db
from app.models.user import User
from app.routes.forms import UserForm
from app.services.user_service import UserService  # 导入服务层

admin = Blueprint('admin', __name__)


# 管理员权限检查装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            # 权限不足提示
            flash('您没有访问该页面的权限')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@admin.route('/dashboard')
@login_required
def dashboard():
    # 统计数据：总用户数、管理员数、普通用户数
    total_users = User.query.count()
    admin_users = User.query.filter_by(is_admin=True).count()
    normal_users = total_users - admin_users

    # 传递数据到模板
    return render_template(
        'admin/dashboard.html',
        title='控制台',
        total_users=total_users,
        admin_users=admin_users,
        normal_users=normal_users
    )


@admin.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    # 模板中也要使用新的变量名
    return render_template('admin/users.html', title='用户管理', users=all_users)


@admin.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        # 使用服务层创建用户
        if UserService.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                real_name=form.real_name.data,
                is_admin=form.is_admin.data
        ):
            return redirect(url_for('admin.users'))

    return render_template('admin/create_user.html', title='创建用户', form=form)


@admin.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    # 实例化表单，并传入当前用户ID
    form = UserForm(user_id=user.id, obj=user)
    # 编辑时，密码字段不应是必填的
    form.password.validators = []
    form.password2.validators = []

    if form.validate_on_submit():
        # 不允许修改admin用户的管理员权限
        if user.username == 'admin' and not form.is_admin.data:
            flash('无法移除admin用户的管理员权限')
            return redirect(url_for('admin.edit_user', user_id=user_id))

        # 将表单数据 populate 到用户对象
        form.populate_obj(user)

        # 如果提供了新密码，则更新密码
        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash('用户信息更新成功')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', title='Edit User', user=user, form=form)


@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.username == 'admin':
        # 不可删除admin
        flash('无法删除admin用户')
        return redirect(url_for('admin.users'))

    db.session.delete(user)
    db.session.commit()
    # 删除成功
    flash('用户删除成功')
    return redirect(url_for('admin.users'))


@admin.route('/profile')
@login_required
def user_profile():
    return render_template('admin/profile.html', title='个人中心')
