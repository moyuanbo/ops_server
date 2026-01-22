#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from apps.config import MYSQL_CONFIG
from apps.server.asset_manager import create_management_bp

mysql_bp = create_management_bp(
    bp_name='mysql_management',
    url_prefix='/mysql_management',
    list_template='server/mysql_list.html',
    add_template='server/add_mysql.html',
    modify_template='server/modify_mysql.html',
    table_config=MYSQL_CONFIG['mysql_list'],
    entity_name='MySQL',
    list_var_name='mysql_s'  # 模板中用mysql_s接收列表数据
)