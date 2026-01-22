#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import json

from flask_login import current_user
from flask_login import login_required
from flask import Blueprint, jsonify, request, render_template, Flask, Response

from apps.models.decorators import admin_required
from apps.ops_game.deploy_game_operation import AddGameApp
from apps.ops_game.operation_game_app import OperationGameApp
from apps.ops_game.filter_game_list import GameListFilter
from apps.models.logger_manager import LoggerManager
from apps.ops_game.update_client import UpdateClientApp
from apps.ops_game.db_utils import GameDBUtil

# 实例化类（创建实例）
query_game_operation_info = GameListFilter()
# 查询区服列表
get_games = query_game_operation_info.get_games
# 查询游戏服有哪些数据，用作选择提交
query_game_db = query_game_operation_info.query_game_db
# 查询要操作的区服列表
query_game_list = GameDBUtil.query_game_list
# 查询游戏服列表下的渠道列表
get_distinct_channels = query_game_operation_info.get_distinct_channels
# 查询游戏服列表下的区服类型
get_distinct_server_type = query_game_operation_info.get_distinct_server_type
# 查询渠道列表
get_channel_list = query_game_operation_info.get_channel_list
# 查询区服类型
get_game_type_list = query_game_operation_info.get_game_type_list
# 查询最大的区服number
get_max_game = query_game_operation_info.get_max_game

# 加载日志模块
logger = LoggerManager()

# 创建 Flask 应用
ops_game = Flask(__name__, template_folder="templates", static_folder="static")

# 定义一个 Blueprint
operation_bp = Blueprint('ops_game', __name__, url_prefix='/ops_game')


@operation_bp.route('/operate')
@login_required
@admin_required
def game_operation():
    # 游戏服操作参数
    script_alias = request.args.get('script', '')
    # 如果是同步代码就接受 同步模式参数(update|reload)
    rsync_mode = request.args.get('rsync_mode', '')
    if rsync_mode:
        # 记录日志信息
        logger.info(f"执行同步操作，模式：{rsync_mode}，脚本参数：{script_alias}")
    else:
        logger.info(f"执行游戏服脚本操作，脚本参数：{script_alias}")

    operation_game = OperationGameApp()
    return ops_game.response_class(
        operation_game.operation_game(script=script_alias, rsync_mode=rsync_mode),
        mimetype='text/event-stream'
    )


@operation_bp.route('/generator_list')
@login_required
@admin_required
def generator_list():
    return render_template('ops_game/generate_list.html', title='生成列表')

@operation_bp.route('/update_game')
@login_required
@admin_required
def update_game():
    return render_template('ops_game/update_game.html', title='更新游戏')

@operation_bp.route('/battle_game')
@login_required
@admin_required
def battle_game():
    return render_template('ops_game/update_battle.html', title='更新录像')

@operation_bp.route('/reload_game')
@login_required
@admin_required
def reload_game():
    return render_template('ops_game/reload_game.html', title='热更游戏')

# 获取游戏服列表下的渠道列表
@operation_bp.route('/api/channel_name_list')
@login_required
@admin_required
def get_channels():
    return jsonify(get_distinct_channels())

# 获取游戏服列表下的渠道列表下的区服类型
@operation_bp.route('/api/game_type')
@login_required
@admin_required
def get_server_type():
    channel_name = request.args.get('channel_name', '')
    if not channel_name:
        return jsonify([])
    return jsonify(get_distinct_server_type(channel_name))

# 获取游戏服列表下的渠道列表下的区服类型下的区服
@operation_bp.route('/api/game_nu')
@login_required
@admin_required
def get_games_api():
    channel_name = request.args.get('channel_name', '')
    server_type = request.args.get('server_type', '')
    if not channel_name or not server_type:
        return jsonify([])
    return jsonify(get_games(channel_name, server_type))

@operation_bp.route('/submit', methods=['POST'])
@login_required
@admin_required
def submit_selection():
    data = request.get_json()
    # 新增接收更新方式参数
    update_mode = data.get('update_mode') or None
    channel_name = data.get('channel_name') or None  # 空字符串转为 None
    server_type = data.get('server_type') or None
    game_nu = data.get('game_nu') or None

    # 传递update_mode参数到查询方法
    rows, filter_list = query_game_db(
        channel_name=channel_name,
        server_type=server_type,
        game_nu=game_nu,
        update_mode=update_mode
    )
    results = [f"{r['channel_name']} - {r['server_type']} - {r['game_nu']}" for r in rows] or ["未找到匹配的区服"]
    if '未找到匹配的区服' in results:
        return jsonify({'results': results})
    filter_list = query_game_list()
    return filter_list


@operation_bp.route('/query_list')
@login_required
@admin_required
def query_data():
    try:
        return query_game_list()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 前端更新页面
@operation_bp.route('/update_client')
@login_required
def update_client():
    """前端更新页面（仅管理员可访问）"""
    if not current_user.is_admin:
        return "无管理员权限", 403
    return render_template('ops_game/update_client.html', title='前端更新')

# 执行前端更新操作（SSE实时返回日志）
@operation_bp.route('/operate_client')
@login_required
def operate_client():
    """执行前端更新操作"""
    if not current_user.is_admin:
        return "无管理员权限", 403

    # 获取前端传入的渠道参数
    channel = request.args.get('channel', '').strip()
    if not channel:
        return Response(
            f"data: {json.dumps({'status': 'error', 'message': '未传入更新渠道参数'})}\n\n",
            mimetype='text/event-stream'
        )

    logger.info(f"用户 {current_user.username} 启动前端更新操作")
    update_app = UpdateClientApp()
    # 返回SSE响应
    return Response(
        update_app.start_update(channel=channel),
        mimetype='text/event-stream'
    )

# 获取渠道列表
@operation_bp.route('/add/api/channel_name_list')
@login_required
@admin_required
def add_get_channels():
    return jsonify(get_channel_list())

# 获取区服类型列表
@operation_bp.route('/add/api/game_type_list')
@login_required
@admin_required
def add_get_type():
    return jsonify(get_game_type_list())

# 获取做大区服number
@operation_bp.route('/add/api/query_max_game')
@login_required
@admin_required
def query_max_game():
    channel_name = request.args.get('channel_name', '')
    server_type = request.args.get('server_type', '')
    if not channel_name or not server_type:
        return jsonify(None)  # 缺少参数时返回None
    max_game = get_max_game(channel_name, server_type)
    return jsonify(max_game)  # 直接返回最大值（int）或None

@operation_bp.route('/add_index')
@login_required
@admin_required
def add_index():
    return render_template('ops_game/add_index.html', title='添加游戏服')

@operation_bp.route('/add/game', methods=['POST'])
@login_required
@admin_required
def add_game():
    data = request.get_json()
    channel_name = data.get('channel_name') or None
    game_type = data.get('server_type') or None
    max_game = data.get('max_game') or None
    init_number = data.get('init_number') or None

    # 添加区服列表
    add_game_app = AddGameApp(channel_name, game_type, max_game, init_number)
    add_status, message = add_game_app.add_game_info()
    if add_status != 'success':
        return jsonify({'status': add_status, 'message': message})

    filter_list = query_game_list()

    return jsonify({'status': 'success', 'message': filter_list})