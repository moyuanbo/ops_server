#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from apps.server.asset_manager import create_management_bp

server_bp = create_management_bp(
    bp_name='server_management',
    url_prefix='/server',
    list_template='server/server_list.html',
    add_template='server/add_server.html',
    modify_template='server/modify_server.html',
    table_config=None,  # 服务器模块使用默认表配置
    entity_name='服务器',
    list_var_name='servers'  # 模板中用servers接收列表数据
)