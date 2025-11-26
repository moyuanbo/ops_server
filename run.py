# run.py
import os
from app import create_app

# 从环境变量获取配置，默认为开发环境
config_name = os.environ.get('FLASK_ENV', 'default')
app = create_app()

if __name__ == '__main__':
    # 生产环境不应使用Flask内置服务器，这里仅为开发方便
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 8080)),
        debug=app.config['DEBUG']
    )