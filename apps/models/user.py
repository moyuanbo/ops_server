#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import re
import pytz
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from apps.config import ZONE_TIME
from apps.extensions import db, login_manager
from apps.models.logger_manager import LoggerManager

logger = LoggerManager()
# 设置时区（新增）
zone_time = pytz.timezone(ZONE_TIME)

class UserManager(UserMixin, db.Model):
    __tablename__ = 'ops_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    real_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now().replace(tzinfo=zone_time))
    last_login = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=lambda: datetime.now().replace(tzinfo=zone_time))
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')

    # 添加哈希算法版本跟踪,设置为可空+默认值，兼容现有数据
    hash_algorithm = db.Column(db.String(20), default='pbkdf2:sha256', nullable=True)

    def set_password(self, password):
        """设置密码（新用户/修改密码时执行）"""
        # 调用优化后的密码验证函数
        password_check = self.is_password_strong(password)
        if not password_check['valid']:
            # 拼接错误信息并抛出异常
            error_msg = "密码强度不够：" + "，".join(password_check['errors'])
            raise ValueError(error_msg)

        try:
            # 优先使用scrypt算法
            self.password_hash = generate_password_hash(
                password,
                method='scrypt:32768:8:1',
                salt_length=16
            )
            self.hash_algorithm = 'scrypt'
        except Exception as e:
            logger.warning(f"Scrypt算法不可用，降级到pbkdf2: {str(e)}")
            # 降级使用pbkdf2算法
            self.password_hash = generate_password_hash(
                password,
                method='pbkdf2:sha256:100000',
                salt_length=16
            )
            self.hash_algorithm = 'pbkdf2:sha256'

        self.password_changed_at = datetime.now(timezone.utc)
        self.failed_login_attempts = 0  # 重置失败尝试次数

    def check_password(self, password):
        """验证密码（兼容旧用户，不检查hash_algorithm）"""
        if self.account_locked:
            return False

        # 登录时只验证密码，不处理hash_algorithm字段
        result = check_password_hash(self.password_hash, password)

        if not result:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:
                self.account_locked = True
            # 关键：使用try-except避免字段缺失错误
            try:
                db.session.commit()
            except Exception as e:
                logger.warning(f"更新登录失败次数时出错（兼容模式）: {str(e)}")
                db.session.rollback()
        return result

    def upgrade_password_hash(self):
        """手动升级密码哈希算法（可选）"""
        if not self.hash_algorithm or self.hash_algorithm == 'pbkdf2:sha256':
            # 需要原密码才能升级，这里可以记录待升级状态
            logger.info(f"用户 {self.username} 密码哈希需要升级")
            return False
        return True

    @staticmethod
    def is_password_strong(password):
        """验证密码强度（新用户/修改密码时执行）返回验证结果和错误信息"""
        errors = []
        if len(password) < 8:
            errors.append("长度至少8位")
        if not re.search(r'[A-Z]', password):
            errors.append("需包含至少一个大写字母")
        if not re.search(r'[a-z]', password):
            errors.append("需包含至少一个小写字母")
        if not re.search(r'[0-9]', password):
            errors.append("需包含至少一个数字")
        if not re.search(r'[^A-Za-z0-9]', password):
            errors.append("需包含至少一个特殊字符（如!@#$等）")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    @staticmethod
    def lock_user(user_id):
        """锁定用户，返回包含状态和消息的字典"""
        try:
            user = UserManager.query.filter_by(id=user_id, is_deleted=False).first()
            if not user:
                return {'success': False, 'msg': '用户不存在或已删除'}
            if user.account_locked:
                return {'success': False, 'msg': '用户已处于锁定状态'}
            user.account_locked = True
            db.session.commit()
            return {'success': True, 'msg': '用户锁定成功'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"锁定用户失败：{e}")  # 使用日志记录具体错误
            return {'success': False, 'msg': '系统错误，锁定失败'}

    @staticmethod
    def unlock_user(user_id):
        """解锁用户，返回包含状态和消息的字典"""
        try:
            user = UserManager.query.filter_by(id=user_id, is_deleted=False).first()
            if not user:
                return {'success': False, 'msg': '用户不存在或已删除'}
            if not user.account_locked:
                return {'success': False, 'msg': '用户已处于解锁状态'}
            user.account_locked = False
            db.session.commit()
            return {'success': True, 'msg': '用户解锁成功'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"解锁用户失败：{e}")
            return {'success': False, 'msg': '系统错误，解锁失败'}

    @staticmethod
    def delete_user(user_id):
        """删除用户，返回包含状态和消息的字典"""
        try:
            user = UserManager.query.filter_by(id=user_id, is_deleted=False).first()
            if not user:
                return {'success': False, 'msg': '用户不存在或已删除'}
            # 禁止删除当前登录管理员（避免误删自己导致无法登录）
            from flask_login import current_user
            if user.id == current_user.id:
                return {'success': False, 'msg': '不能删除当前登录的管理员账号'}
            user.is_deleted = True
            db.session.commit()
            return {'success': True, 'msg': '用户删除成功'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除用户失败：{e}")
            return {'success': False, 'msg': '系统错误，删除失败'}

    def __repr__(self):
        return f'<User {self.username} ({self.real_name})>'

@login_manager.user_loader
def load_user(user_id):
    try:
        # 验证用户ID格式
        if not user_id or not user_id.isdigit():
            logger.warning(f"无效的用户ID格式: {user_id}")
            return None

        user_id_int = int(user_id)
        # 查询用户
        user = UserManager.query.get(user_id_int)

        # 检查用户是否存在且账号未被锁定
        if user:
            if user.account_locked:
                logger.warning(f"用户 {user.username} (ID: {user_id_int}) 账号已被锁定")
                return None
            if user.is_deleted:
                logger.warning(f"用户 {user.username} (ID: {user_id_int}) 账号已被删除")
                return None

            return user


        logger.warning(f"用户ID {user_id_int} 不存在")
        return None

    except ValueError as e:
        logger.error(f"用户ID转换失败: {user_id}, 错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"加载用户失败: {user_id}, 错误: {str(e)}")
        return None