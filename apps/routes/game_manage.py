#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from apps.config import MYSQL_CONFIG
from apps.server.asset_manager import create_management_bp

game_bp = create_management_bp(
    bp_name='game_management',
    url_prefix='/game_management',
    list_template='server/game_list.html',
    add_template='server/add_game.html',
    modify_template='server/modify_game.html',
    table_config=MYSQL_CONFIG['game_list_table'],
    entity_name='游戏服',
    list_var_name='game_ls'
)