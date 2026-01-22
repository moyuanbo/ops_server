#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
from pathlib import Path

from apps import create_app


app = create_app()

# 获取脚本所在目录的路径对象
script_dir = Path(__file__).parent
# 切换到脚本所在目录
os.chdir(script_dir)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 8080))
