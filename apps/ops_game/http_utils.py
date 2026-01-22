#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import requests


class HttpUtil:
    """HTTP请求工具类"""
    @staticmethod
    def request_with_log(url, logger, output_queue, action="请求"):
        """带日志和输出的HTTP请求"""
        try:
            output_queue.put({
                "status": "info",
                "message": f"发起{action}: {url}",
                "data": {"url": url}
            })
            logger.info(f"发起{action}: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            msg = f"{action}成功信息 -> {response.text}"
            output_queue.put({
                "status": "success",
                "message": msg,
                "data": {"url": url, "status_code": response.text}
            })
            logger.info(msg)
            return True

        except requests.exceptions.Timeout:
            msg = f"{action}超时: {url}（超过10秒）"
        except Exception as e:
            msg = f"{action}失败: {str(e)}"

        output_queue.put({
            "status": "error",
            "message": msg,
            "data": {"url": url}
        })
        logger.error(msg)
        return False
