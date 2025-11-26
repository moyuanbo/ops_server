# app/config.py
import os
from dotenv import load_dotenv
import secrets

# 加载环境变量
load_dotenv()


class BaseConfig:
    # 生产环境使用随机生成的密钥，通过环境变量设置
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # MySQL数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis数据库配置
    REDIS_URL = os.environ.get('REDIS_URL')

    # 会话配置
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "True") == "True"
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    SESSION_COOKIE_HTTPONLY = True  # 防止JavaScript访问cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # 防止CSRF

    # CSRF配置
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF令牌有效期1小时


class DevConfig(BaseConfig):
    DEBUG = True


class ProdConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    # 生产环境下必须设置环境变量
    SECRET_KEY = os.environ.get('SECRET_KEY')
    assert SECRET_KEY != secrets.token_hex(32), "生产环境必须设置SECRET_KEY环境变量"


# 根据环境变量选择配置
config = {
    'development': DevConfig,
    'production': ProdConfig,
    'default': ProdConfig
}
