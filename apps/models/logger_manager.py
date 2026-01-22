#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from apps import config

class LoggerManager:
    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._init_logger()
        return cls._instance

    def _init_logger(self):
        # 创建日志目录
        os.makedirs(config.LOG_DIR, mode=0o755, exist_ok=True)

        # 设置日志文件路径
        log_file = os.path.join(config.LOG_DIR, "apps.log")

        # 创建 TimedRotatingFileHandler
        handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",  # 每天午夜轮转
            interval=1,       # 间隔1天
            backupCount=config.LOG_BACKUP_COUNT,  # 保留30天
            encoding='utf-8'
        )

        # 设置日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # 配置 logger
        self._logger = logging.getLogger('app_logger')
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(handler)

    def info(self, message):
        self._logger.info(message)

    def error(self, message):
        self._logger.error(message)

    def warning(self, message):
        self._logger.warning(message)

    def debug(self, message):
        self._logger.debug(message)

    def critical(self, message):
        self._logger.critical(message)
