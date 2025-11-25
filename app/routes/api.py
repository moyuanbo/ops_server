# app/routes/api.py
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app.models.user import User
from app.services.user_service import UserService
from app.routes.forms import UserForm
from functools import wraps

api = Blueprint('api', __name__, url_prefix='/api/v1')


# API管理员权限装饰器
def api_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        return f(*args, **kwargs)

    return decorated_function


# API认证装饰器
def api_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': '请先登录'}), 401
        return f(*args, **kwargs)

    return decorated_function


# 获取用户列表API
@api.route('/users', methods=['GET'])
@login_required
@api_admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'email': user.email,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    } for user in users])


# 创建用户API
@api.route('/users', methods=['POST'])
@login_required
@api_admin_required
def create_api_user():
    data = request.get_json()

    # 验证数据
    form = UserForm(data=data)
    if not form.validate():
        return jsonify({'error': '数据验证失败', 'details': form.errors}), 400

    # 创建用户
    if UserService.create_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            real_name=data.get('real_name'),
            is_admin=data.get('is_admin', False)
    ):
        return jsonify({'message': '用户创建成功'}), 201
    return jsonify({'error': '创建用户失败'}), 500

# 其他API接口...