# app/routes/auth.py
import os
from datetime import timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.models.user import User
from app.routes.forms import LoginForm


# 创建蓝图（limiter已在应用工厂初始化，直接使用装饰器）
auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # 登录限流：每分钟5次
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.users'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash('无效的用户名或密码')
            return redirect(url_for('auth.login'))

        # 更新登录时间
        user.update_last_login()
        db.session.commit()

        # 登录（记住我：1小时有效期）
        timeout = int(os.environ.get('SESSION_TIMEOUT'))
        login_user(user, remember=form.remember_me.data, duration=timedelta(hours=timeout))
        print(timeout)

        # 处理跳转
        next_page = request.args.get('next')
        return redirect(next_page or url_for('admin.users'))

    return render_template('auth/login.html', title='登录', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
