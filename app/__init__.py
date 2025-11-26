import os

from flask import Flask

from app.config import ProdConfig, DevConfig
from app.extensions import init_extensions

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    env = os.environ.get("FLASK_ENV", "production")
    if env == "development":
        app.config.from_object(DevConfig)
    else:
        app.config.from_object(ProdConfig)

    # 调用扩展
    init_extensions(app)

    # 注册蓝图
    from app.routes.auth import auth as auth_bp
    from app.routes.admin import admin as admin_bp
    from app.routes.api import api as api_bp  # 导入API蓝图

    app.register_blueprint(api_bp)  # 注册API蓝图
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
