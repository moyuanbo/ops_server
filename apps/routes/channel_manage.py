#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from apps.config import MYSQL_CONFIG
from apps.server.asset_manager import create_management_bp

# 使用工厂函数创建蓝图，只传入差异化参数
channel_bp = create_management_bp(
    bp_name='channel_management',
    url_prefix='/channel_management',
    list_template='server/channel_list.html',
    add_template='server/add_channel.html',
    modify_template='server/modify_channel.html',
    table_config=MYSQL_CONFIG['channel_list'],
    entity_name='渠道',
    list_var_name='channels'  # 模板中用channels接收列表数据
)