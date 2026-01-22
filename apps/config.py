#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import redis
from dotenv import load_dotenv
from datetime import timedelta

# 获取脚本位置
bash_script_dir = os.getcwd()

# 加载环境变量
load_dotenv()
APP_VERSION = '1.0.0'

# 日志配置
LOG_DIR = os.path.join(bash_script_dir, 'logs')
LOG_BACKUP_COUNT = 30  # 保留最近30天的日志
# 最大线程数
MAX_WORKERS = 10
# 时区配置
ZONE_TIME = 'Asia/Shanghai'

# SQLAlchemy连接配置
mysql_user = os.environ.get('OPS_MYSQL_USER')
mysql_pass = os.environ.get('OPS_MYSQL_PASS')
mysql_host = os.environ.get('OPS_MYSQL_IP')
db_name = os.environ.get('OPS_DB_NAME')

# redis限流
redis_ip = os.environ.get('REDIS_IP')
redis_port = os.environ.get('REDIS_PORT')
redis_pass = os.environ.get('REDIS_PASS')
redis_db = os.environ.get('REDIS_DB')
redis_url = "redis://:{0}@{1}:{2}/{3}".format(redis_pass, redis_ip, redis_port, redis_db)

# MySQL数据配置
MYSQL_CONFIG = {
    'host': mysql_host,
    'user': mysql_user,
    'passwd': mysql_pass,
    'db_name': db_name,
    'port': 3306,
    'game_list_table': 'game_server_list',
    'operation_game_list': 'operation_game_list',
    'server_list': 'server_list',
    'channel_list': 'channel_list',
    'reload_url_list': 'reload_url_list',
    'mysql_list': 'mysql_list',
    'game_type_list': 'game_type_list',
}

OPERATION_PARAMETER = {
    'status': '检查游戏服状态',
    'stop': '停服',
    'start': '起服',
    'update': '更新',
    'battle': '更新录像',
    'reload': '热更',
    'rsync': '同步代码',
    'initial': '部署'
}

# SSH 配置（请根据实际情况修改）
CLIENT_INFO = {
    'ip': os.environ.get('CLIENT_IP'),
    'port': 22,
    'user': 'root',
    'key_path': os.path.join(bash_script_dir,'jump_server'),
}
# 前端更新命令
CLIENT_DIR = " /data/client/web/ | grep -Ev '^sending|^sent|^total|^$|^\\./'"
CLIENT_UPDATE_CMD = {
    'Wechat': 'rsync -av /data/client/web/zhengshi/indexWechat.html' + CLIENT_DIR,
    'ALL': 'rsync -av /data/client/web/zhengshi/' + CLIENT_DIR,
    'indexIos': 'rsync -av /data/client/web/zhengshi/indexIos.html' + CLIENT_DIR,
    'indexBytedance': 'rsync -av /data/client/web/zhengshi/indexBytedance.html' + CLIENT_DIR,
    'indexBytedanceGs': 'rsync -av /data/client/web/zhengshi/indexBytedanceGs.html' + CLIENT_DIR,
    'indexWechatGs': 'rsync -av /data/client/web/zhengshi/indexWechatGs.html' + CLIENT_DIR,
    'indexIos_tishen': 'rsync -av /data/client/web/zhengshi/indexIos_tishen.html' + CLIENT_DIR,
}

# 本地脚本白名单
EXECUTOR_SCRIPTS = {
    'default_script': os.path.join(bash_script_dir, 'apps', 'scripts', 'operation_game.sh'),
    'initial_game': os.path.join(bash_script_dir, 'apps', 'scripts', 'initial_game.sh'),
}

SVN_CONFIG = {
    'svn_dir': os.path.join(bash_script_dir, 'svn_game_update'),
    'svn_com': f"svn --username={os.environ.get('SVN_USER')} --password={os.environ.get('SVN_PASS')} --no-auth-cache",
    'svn_url': os.environ.get('SVN_URL'),
}

# 月份映射
month_list = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sept': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}

class Config:
    """基础配置类"""
    # 生成安全的随机密钥，不要硬编码
    SECRET_KEY = os.getenv('SECRET_KEY')

    # ========== CSRF 配置优化 ==========
    # 加载JWT密钥: 复用SECRET_KEY密钥，避免单独维护
    JWT_SECRET_KEY = os.environ.get('SECRET_KEY')
    # 加载过期时间（转成整数，默认3600秒）
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 7200)))
    JWT_TOKEN_LOCATION = ['cookies']  # JWT存储在Cookie中
    JWT_COOKIE_HTTPONLY = True  # 禁止前端JS读取Cookie中的JWT，防XSS
    JWT_COOKIE_SAMESITE = 'Lax'  # 限制Cookie跨站传递，防CSRF
    JWT_COOKIE_SECURE = False  # 生产环境开启HTTPS后改为True
    WTF_CSRF_ENABLED = True  # 启用CSRF保护（生产环境建议开启）
    # 加载WTF密钥: 复用SECRET_KEY密钥，避免单独维护
    # ========== JWT 自带的CSRF保护（替代WTF-CSRF） ==========
    JWT_CSRF_IN_COOKIES = True  # CSRF Token存储在Cookie（XSRF-TOKEN）
    JWT_CSRF_CHECK_FORM = True  # 支持从表单/请求头获取CSRF Token
    JWT_CSRF_METHODS = ['POST', 'PUT', 'DELETE', 'PATCH']  # 仅对写操作做CSRF验证

    # 数据库URI（拼接.env中的数据库信息）
    SQLALCHEMY_DATABASE_URI = ("mysql+pymysql://{0}:{1}@{2}/{3}?charset=utf8mb4".format(
                            mysql_user, mysql_pass, mysql_host, db_name))

    # 数据库配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_recycle': 1800,
        'pool_pre_ping': True,
        'pool_timeout': 30,
        'echo': False,    # 不显示SQL日志
        'isolation_level': 'READ COMMITTED' # 添加事务隔离级别
    }

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# 配置验证函数
def validate_config(config_obj):
    """验证配置的有效性"""
    # 验证数据库连接池关键参数
    engine_opts = config_obj.SQLALCHEMY_ENGINE_OPTIONS
    required_pool_keys = ['pool_size', 'max_overflow']
    for key in required_pool_keys:
        if key not in engine_opts:
            raise ValueError(f"SQLALCHEMY_ENGINE_OPTIONS 必须包含 {key}")

    # 验证MySQL核心配置
    required_mysql_keys = ['host', 'user', 'passwd', 'db_name', 'port']
    for key in required_mysql_keys:
        if not MYSQL_CONFIG.get(key):
            raise ValueError(f"MySQL配置缺失关键项: {key}")

# 初始化并验证配置
try:
    validate_config(Config)
except ValueError as e:
    print(f"配置验证失败: {e}")
    raise
