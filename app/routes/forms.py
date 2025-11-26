from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired('用户名不能为空')])
    password = PasswordField('密码', validators=[DataRequired('密码不能为空')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class UserForm(FlaskForm):
    username = StringField('登录用户名', validators=[
        DataRequired('登录用户名不能为空'),
        Length(min=4, max=64, message='用户名长度必须在4-64位之间')
    ])
    real_name = StringField('中文姓名', validators=[  # 中文姓名字段
        DataRequired('中文姓名不能为空'),
        Length(min=2, max=64, message='中文姓名长度必须在2-64位之间')
    ])
    email = StringField('邮箱', validators=[
        DataRequired('邮箱不能为空'),
        Email('请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired('密码不能为空'),
        Length(min=6, message='密码长度不能少于6位')
    ])
    password2 = PasswordField('重复密码', validators=[
        DataRequired('请重复密码'),
        EqualTo('password', message='两次输入的密码不一致')
    ])
    is_admin = BooleanField('设为管理员')
    submit = SubmitField('提交')

    def __init__(self, user_id=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.user_id:
            raise ValidationError('该登录用户名已被使用，请更换')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.user_id:
            raise ValidationError('该邮箱已被注册，请更换')

    # 新增：验证中文姓名（可选，可根据需求添加特殊字符限制）
    def validate_real_name(self, real_name):
        # 示例：禁止包含特殊字符（可根据需求调整）
        import re
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_]+$', real_name.data):
            raise ValidationError('中文姓名只能包含汉字、字母、数字和下划线')
