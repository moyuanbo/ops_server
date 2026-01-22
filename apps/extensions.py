#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect

from apps import config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# 初始化限流器
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=config.redis_url
)

jwt = JWTManager()       # 初始化JWT
csrf = CSRFProtect()     # 初始化CSRF保护

def init_extensions(app):
    db.init_app(app)
    limiter.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "请登录以访问此页面！"
    login_manager.login_message_category = 'info'
