#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask

from flask_login import LoginManager

from apps.config import Config
from apps.extensions import init_extensions, jwt, csrf

# 初始化扩展
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

app = Flask(__name__)
# ========== 核心安全配置 ==========
# 基础密钥（CSRF/JWT均依赖，生产环境务必用环境变量）
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-strong-secret-key-123'
# 2. JWT配置
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret-key-456'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']  # JWT存储到Cookie（防XSS）
app.config['JWT_COOKIE_CSRF_PROTECT'] = True    # 开启JWT的CSRF保护
app.config['JWT_COOKIE_SECURE'] = True          # 生产环境开启（仅HTTPS传输）
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'       # 防CSRF（Strict更严格）

# 创建应用
user_system = Flask(__name__, template_folder="templates", static_folder="static")

def configure_logging(flask_app):
    """配置日志系统"""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler(
        'logs/ops_game_server.log',
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(os.getenv('LOG_LEVEL'))

    flask_app.logger.addHandler(file_handler)
    flask_app.logger.setLevel(os.getenv('LOG_LEVEL'))
    flask_app.logger.info('Ops Game Server startup')

def register_blueprints(flask_app):
    """注册蓝图"""
    from apps.routes.auth import auth as auth_bp
    from apps.routes.user_manage import admin_bp
    # 新增API蓝图
    from apps.api.user import api as api_bp
    # 操作游戏服蓝图
    from apps.routes.game_operation import operation_bp
    # 服务器蓝图
    from apps.routes.server_manage import server_bp
    # 渠道蓝图
    from apps.routes.channel_manage import channel_bp
    # MySQL蓝图
    from apps.routes.mysql_manage import mysql_bp
    # 游戏服蓝图
    from apps.routes.game_manage import game_bp

    flask_app.register_blueprint(auth_bp, url_prefix='/auth')
    flask_app.register_blueprint(admin_bp, url_prefix='/admin')
    flask_app.register_blueprint(api_bp, url_prefix='/api')  # API路由前缀
    flask_app.register_blueprint(operation_bp, url_prefix='/ops_game') # 游戏服路由前缀
    flask_app.register_blueprint(server_bp, url_prefix='/server')
    flask_app.register_blueprint(channel_bp, url_prefix='/channel')
    flask_app.register_blueprint(mysql_bp, url_prefix='/mysql')
    flask_app.register_blueprint(game_bp, url_prefix='/game')


def register_error_handlers(flask_app):
    """注册错误处理器"""
    from apps.models.errors import error_404, error_403, error_500, handle_sql_error

    flask_app.register_error_handler(404, error_404)
    flask_app.register_error_handler(403, error_403)
    flask_app.register_error_handler(500, error_500)
    flask_app.register_error_handler(Exception, handle_sql_error)

def create_app():
    """应用工厂函数"""
    user_system.config.from_object(Config)

    # ===== 先初始化Redis会话扩展 =====
    # 初始化扩展
    init_extensions(user_system)
    # ===== 初始化 JWT 扩展 =====
    jwt.init_app(user_system)
    jwt.init_app(app)  # 初始化JWT
    csrf.init_app(app)  # 初始化CSRF保护

    # 配置日志
    configure_logging(user_system)

    # 注册蓝图
    register_blueprints(user_system)

    # 注册错误处理器
    register_error_handlers(user_system)

    with user_system.app_context():
        # 验证数据库连接池
        from apps.utils.db_utils import get_connection_pool_status, test_database_connection
        if os.getenv('FLASK_CONFIG') == 'production':
            test_database_connection()
            get_connection_pool_status()

    return user_system
