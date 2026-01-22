#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import secrets
import string
import re


def generate_strong_password(length=12):
    """生成符合强度要求的随机密码"""
    if length < 8:
        length = 8

    # 确保包含所有类型的字符
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = '!@#$%^&*()_-+=[]{}|;:,.<>?'

    # 至少包含每种类型的一个字符
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # 填充剩余字符
    all_chars = uppercase + lowercase + digits + special
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # 打乱顺序
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)


def validate_password(password):
    """验证密码强度，返回详细的错误信息"""
    errors = []

    if len(password) < 8:
        errors.append("密码长度至少8位")

    if not re.search(r'[A-Z]', password):
        errors.append("密码需包含大写字母")

    if not re.search(r'[a-z]', password):
        errors.append("密码需包含小写字母")

    if not re.search(r'[0-9]', password):
        errors.append("密码需包含数字")

    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append("密码需包含特殊字符")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'strength': calculate_password_strength(password)
    }


def calculate_password_strength(password):
    """计算密码强度分数（0-100）"""
    strength = 0

    # 长度加分
    if len(password) >= 8:
        strength += min(len(password) - 7, 10)

    # 字符类型加分
    if re.search(r'[A-Z]', password):
        strength += 20
    if re.search(r'[a-z]', password):
        strength += 20
    if re.search(r'[0-9]', password):
        strength += 20
    if re.search(r'[^A-Za-z0-9]', password):
        strength += 20

    # 组合加分
    char_types = 0
    if re.search(r'[A-Z]', password):
        char_types += 1
    if re.search(r'[a-z]', password):
        char_types += 1
    if re.search(r'[0-9]', password):
        char_types += 1
    if re.search(r'[^A-Za-z0-9]', password):
        char_types += 1

    strength += (char_types - 1) * 5

    return min(strength, 100)


def get_password_strength_label(strength):
    """根据强度分数返回标签"""
    if strength >= 80:
        return '强', 'success'
    elif strength >= 50:
        return '中', 'warning'
    else:
        return '弱', 'danger'
