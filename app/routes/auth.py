# app/routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
# 1. 从 urllib.parse 导入 urlparse
from urllib.parse import urlparse
from datetime import datetime, timezone
from app import db
from app.models.user import User
from app.routes.forms import LoginForm

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # 3. 实例化 LoginForm
    form = LoginForm()

    # 4. 使用表单的 validate_on_submit() 方法
    if form.validate_on_submit():
        # 5. 从表单对象中获取数据
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('用户名或密码错误')
            # 6. 验证失败时，重定向回登录页
            return redirect(url_for('auth.login'))

        # 7. 使用表单中的 remember_me 数据
        login_user(user, remember=remember_me)

        next_page = request.args.get('next')
        # 8. 使用新导入的 urlparse 函数
        if not next_page or urlparse(next_page).netloc != '':
            if user.is_admin:
                next_page = url_for('admin.dashboard')
            else:
                next_page = url_for('admin.user_profile')

        # 更新最后登录时间
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        return redirect(next_page)

    # 9. GET 请求时，渲染模板并传入表单对象
    return render_template('auth/login.html', title='Sign In', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
