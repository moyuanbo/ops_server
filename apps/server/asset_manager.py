#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from typing import List, Dict, Optional

from flask_login import login_required
from apps.models.decorators import admin_required
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify

from apps.models.operation_mysql import MysqlConfig
from apps.models.logger_manager import LoggerManager
from apps.config import MYSQL_CONFIG

# 通用类型映射
COMMON_TYPE_MAPPING = {
    'port': int,
    'weight': float,
    'is_active': bool,
    'max_connections': int
}


def create_management_bp(
        bp_name,
        url_prefix,
        list_template,
        add_template,
        modify_template,
        table_config,
        entity_name,  # 如"渠道"、"MySQL"、"服务器"
        list_var_name  # 模板中列表变量名，如"channels"、"mysql_s"、"servers"
):
    """
    生成通用管理蓝图的工厂函数
    :param bp_name: 蓝图名称
    :param url_prefix: URL前缀
    :param list_template: 列表页模板路径
    :param add_template: 添加页模板路径
    :param modify_template: 修改页模板路径
    :param table_config: 数据库表配置（MYSQL_CONFIG中的对应项）
    :param entity_name: 实体名称（用于提示信息）
    :param list_var_name: 模板中列表变量的名称
    """
    bp = Blueprint(bp_name, __name__, url_prefix=url_prefix)

    # 列表页面
    @bp.route('/list')
    @login_required
    @admin_required
    def entity_list():
        manager = ServerManager(table_list=table_config, server_info=entity_name) if table_config else ServerManager()
        page = request.args.get('page', 1, type=int)
        per_page = 10
        page = max(1, page)

        entities = manager.get_all_servers(page=page, per_page=per_page)
        total_count = manager.get_server_count()
        total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

        if page > total_pages:
            page = total_pages
            entities = manager.get_all_servers(page=page, per_page=per_page)

        # 构建模板参数（动态使用列表变量名）
        template_kwargs = {
            list_var_name: entities,
            'title': f'{entity_name}管理',
            'current_page': page,
            'total_pages': total_pages,
            'total_count': total_count,
            'per_page': per_page
        }
        return render_template(list_template, **template_kwargs)

    # 添加页面
    @bp.route('/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def add_entity():
        if request.method == 'POST':
            manager = ServerManager(table_list=table_config,
                                    server_info=entity_name) if table_config else ServerManager()
            raw_data = request.form.to_dict()
            raw_data.pop('csrf_token', None)

            converted_data, errors = convert_form_data(raw_data, COMMON_TYPE_MAPPING)
            if errors:
                for err in errors:
                    flash(err, 'danger')
                return render_template(add_template, form_data=raw_data, title=f'添加{entity_name}')

            converted_data.update({
                k: v for k, v in raw_data.items()
                if k not in COMMON_TYPE_MAPPING and v.strip()
            })

            result = manager.add_server(converted_data)
            if result:
                flash(f'{entity_name}添加成功', 'success')
                return redirect(url_for(f'{bp_name}.entity_list'))
            else:
                flash(f'{entity_name}添加失败', 'danger')

        return render_template(add_template, title=f'添加{entity_name}')

    # 修改页面
    @bp.route('/modify/<int:entity_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def modify_entity(entity_id):
        manager = ServerManager(table_list=table_config, server_info=entity_name) if table_config else ServerManager()

        if request.method == 'POST':
            raw_data = request.form.to_dict()
            raw_data.pop('csrf_token', None)

            converted_data, errors = convert_form_data(raw_data, COMMON_TYPE_MAPPING)
            if errors:
                for err in errors:
                    flash(err, 'danger')
                    entity = manager.get_server_by_id(entity_id)
                    return render_template(modify_template, **{
                        list_var_name[:-1]: entity,  # 单数形式（如channel、mysql_info、server）
                        'form_data': raw_data,
                        'title': f'{entity_name}编辑'
                    })

            converted_data.update({
                k: v for k, v in raw_data.items()
                if k not in COMMON_TYPE_MAPPING and v.strip()
            })

            result = manager.update_server(entity_id, converted_data)
            if result:
                flash(f'{entity_name}更新成功', 'success')
                return redirect(url_for(f'{bp_name}.entity_list'))
            else:
                flash(f'{entity_name}更新失败', 'danger')

        entity = manager.get_server_by_id(entity_id)
        if not entity:
            flash(f'{entity_name}不存在', 'danger')
            return redirect(url_for(f'{bp_name}.entity_list'))

        return render_template(modify_template, **{
            list_var_name[:-1]: entity,  # 单数形式
            'title': f'{entity_name}编辑'
        })

    # 删除接口
    @bp.route('/delete/<int:entity_id>', methods=['POST'])
    @login_required
    @admin_required
    def delete_entity(entity_id):
        manager = ServerManager(table_list=table_config, server_info=entity_name) if table_config else ServerManager()
        result = manager.delete_server(entity_id)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': result,
                'msg': f'{entity_name}删除成功' if result else f'{entity_name}删除失败'
            })
        else:
            if result:
                flash(f'{entity_name}删除成功', 'success')
            else:
                flash(f'{entity_name}删除失败', 'danger')
            return redirect(url_for(f'{bp_name}.entity_list'))

    return bp

def convert_form_data(form_data, type_mapping):
    """
    转换表单数据类型
    :param form_data: 原始表单数据（dict，值为字符串）
    :param type_mapping: 类型映射字典，格式：{字段名: 目标类型或转换函数}
    :return: (转换后的数据, 错误信息列表)
    """
    converted_data = {}
    errors = []
    for field, target_type in type_mapping.items():
        # 跳过表单中未提交的字段（非必填项）
        if field not in form_data:
            continue
        raw_value = form_data[field].strip()  # 去除首尾空格
        # 空字符串处理（非必填项可留空，根据业务决定是否设为None）
        if not raw_value:
            converted_data[field] = None
            continue
        try:
            # 特殊处理布尔值（表单复选框通常提交'on'表示选中）
            if target_type is bool:
                converted_value = raw_value.lower() in ('on', 'true', '1')
            else:
                # 通用类型转换（如int, float）
                converted_value = target_type(raw_value)
            converted_data[field] = converted_value
        except (ValueError, TypeError) as e:
            errors.append(f"字段 '{field}' 格式错误，需为{target_type.__name__}类型（错误：{str(e)}）")
    return converted_data, errors

class ServerManager:
    def __init__(self, table_list=MYSQL_CONFIG['server_list'], server_info='服务器'):
        self.logger = LoggerManager()
        self.db_manager = MysqlConfig()
        self.db_manager.connect_pool()
        # 默认为服务器数据库表
        self.server_table = table_list
        self.server_info = server_info

    def get_server_count(self) -> int:
        """获取服务器总记录数（用于分页计算）"""
        try:
            sql = f"SELECT COUNT(*) as count FROM {self.server_table}"
            result = self.db_manager.execute_query(sql)
            return result[0]['count'] if result else 0
        except Exception as e:
            self.logger.error(f"查询{self.server_info}总数失败: {str(e)}")
            return 0

    def get_all_servers(self, page: int = 1, per_page: int = 10) -> List[Dict]:
        """获取分页的服务器列表（新增分页参数）"""
        try:
            # 计算偏移量（避免页码小于1导致的错误）
            offset = max(0, (page - 1) * per_page)
            sql = f"SELECT * FROM {self.server_table} ORDER BY id DESC LIMIT %s OFFSET %s"
            result = self.db_manager.execute_query(sql, (per_page, offset))
            self.logger.info(f"查询{self.server_info}分页数据成功，页码: {page}, 每页数量: {per_page}")
            return result
        except Exception as e:
            self.logger.error(f"查询{self.server_info}分页数据失败: {str(e)}")
            return []

    def get_server_by_id(self, server_id: int) -> Optional[Dict]:
        """通过ID获取服务器信息"""
        try:
            sql = f"SELECT * FROM {self.server_table} WHERE id = %s"
            result = self.db_manager.execute_query(sql, (server_id,))
            self.logger.info(f"查询{self.server_info}ID: {server_id} 成功")
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"查询{self.server_info}ID: {server_id} 失败: {str(e)}")
            return None

    def add_server(self, server_data: Dict) -> bool:
        """添加新服务器"""
        try:
            fields = ', '.join(server_data.keys())
            placeholders = ', '.join(['%s'] * len(server_data))
            sql = f"INSERT INTO {self.server_table} ({fields}) VALUES ({placeholders})"
            affected_rows = self.db_manager.execute_update(sql, tuple(server_data.values()))
            self.logger.info(f"添加{self.server_info}成功，数据: {server_data}")
            return affected_rows > 0
        except Exception as e:
            self.logger.error(f"添加{self.server_info}失败: {str(e)}，数据: {server_data}")
            return False

    def update_server(self, server_id: int, server_data: Dict) -> bool:
        """更新服务器信息"""
        try:
            set_clause = ', '.join([f"{key} = %s" for key in server_data.keys()])
            sql = f"UPDATE {self.server_table} SET {set_clause} WHERE id = %s"
            params = list(server_data.values()) + [server_id]
            affected_rows = self.db_manager.execute_update(sql, tuple(params))
            self.logger.info(f"更新{self.server_info}ID: {server_id} 成功")
            return affected_rows > 0
        except Exception as e:
            self.logger.error(f"更新{self.server_info}ID: {server_id} 失败: {str(e)}")
            return False

    def delete_server(self, server_id: int) -> bool:
        """删除服务器（优化：增加存在性检查）"""
        try:
            # 先检查服务器是否存在
            server = self.get_server_by_id(server_id)
            if not server:
                self.logger.warning(f"删除{self.server_info}失败：ID {server_id} 不存在")
                return False

            # 执行删除
            sql = f"DELETE FROM {self.server_table} WHERE id = %s"
            affected_rows = self.db_manager.execute_update(sql, (server_id,))

            if affected_rows > 0:
                self.logger.info(f"删除{self.server_info}ID: {server_id} 成功")
                return True
            else:
                self.logger.error(f"删除{self.server_info}ID: {server_id} 失败：无记录被删除")
                return False
        except Exception as e:
            self.logger.error(f"删除{self.server_info}ID: {server_id} 失败: {str(e)}")
            return False