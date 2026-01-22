#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
import re

from apps.models.user import UserManager


class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=64)])
    real_name = StringField('真实姓名', validators=[DataRequired(), Length(max=64)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[
        DataRequired(),
        Length(min=8, message='密码长度至少8位')
    ])
    confirm_password = PasswordField('确认密码', validators=[
        DataRequired(),
        EqualTo('password', message='两次密码输入不一致')
    ])
    submit = SubmitField('注册')

    def validate_password(self, field):
        """验证密码强度（仅当填写密码时验证）"""
        if field.data:
            password_check = UserManager.is_password_strong(field.data)
            if not password_check['valid']:
                # 抛出包含具体错误的验证异常
                raise ValidationError(f'密码强度不够：{", ".join(password_check["errors"])}')


class PasswordChangeForm(FlaskForm):
    old_password = PasswordField('原密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[
        DataRequired(),
        Length(min=8, message='密码长度至少8位')
    ])
    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(),
        EqualTo('new_password', message='两次密码输入不一致')
    ])
    submit = SubmitField('修改密码')

    def validate_new_password(self, field):
        """验证新密码强度"""
        password = field.data

        # 密码强度检查
        if not re.search(r'[A-Z]', password) or \
                not re.search(r'[a-z]', password) or \
                not re.search(r'[0-9]', password) or \
                not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError('密码需包含大小写字母、数字和特殊字符')


class UserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=64)])
    real_name = StringField('真实姓名', validators=[DataRequired(), Length(max=64)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码（留空则不修改）', validators=[
        Optional(),  # 允许字段为空
        Length(min=8, message='密码长度至少8位'),
    ])
    password2 = PasswordField('确认密码', validators=[
        EqualTo('password', message='两次密码输入不一致')
    ])
    is_admin = BooleanField('管理员权限')
    submit = SubmitField('保存')

    def validate_password(self, field):
        """验证密码强度（仅当填写密码时验证）"""
        if field.data:
            password_check = UserManager.is_password_strong(field.data)
            if not password_check['valid']:
                # 抛出包含具体错误的验证异常
                raise ValidationError(f'密码强度不够：{", ".join(password_check["errors"])}')

    def validate(self, extra_validators=None):
        """重写验证方法，处理密码字段可选的情况"""
        # 如果密码为空，则移除EqualTo验证
        if not self.password.data:
            # 清空确认密码字段的错误
            if hasattr(self, 'password2'):
                self.password2.errors = []
            if hasattr(self, 'confirm_password'):
                self.confirm_password.errors = []
            # 只验证其他字段
            return super().validate(extra_validators) and True

        # 如果有密码，则执行完整验证
        return super().validate(extra_validators)