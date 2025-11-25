# app/services/user_service.py
from app.extensions import db
from app.models.user import User
from flask import flash


class UserService:
    @staticmethod
    def create_user(username, email, password, real_name, is_admin=False):
        """创建新用户"""
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('该用户名已被使用')
            return False

        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            flash('该邮箱已被注册')
            return False

        # 创建新用户
        new_user = User(
            username=username,
            email=email,
            real_name=real_name,
            is_admin=is_admin
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('用户创建成功')
            return True
        except Exception as e:
            db.session.rollback()
            flash(f'创建用户失败: {str(e)}')
            return False

    @staticmethod
    def update_user(user_id, **kwargs):
        """更新用户信息"""
        user = User.query.get_or_404(user_id)

        # 不允许修改admin用户的管理员权限
        if user.username == 'admin' and 'is_admin' in kwargs and not kwargs['is_admin']:
            flash('无法移除admin用户的管理员权限')
            return False

        # 更新字段
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        # 如果提供了新密码，则更新密码
        if 'password' in kwargs and kwargs['password']:
            user.set_password(kwargs['password'])

        try:
            db.session.commit()
            flash('用户信息更新成功')
            return True
        except Exception as e:
            db.session.rollback()
            flash(f'更新用户失败: {str(e)}')
            return False

    @staticmethod
    def delete_user(user_id):
        """删除用户"""
        user = User.query.get_or_404(user_id)

        # 不能删除admin用户
        if user.username == 'admin':
            flash('无法删除admin用户')
            return False

        try:
            db.session.delete(user)
            db.session.commit()
            flash('用户删除成功')
            return True
        except Exception as e:
            db.session.rollback()
            flash(f'删除用户失败: {str(e)}')
            return False
