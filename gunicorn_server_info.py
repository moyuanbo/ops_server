#!/data/software/jumpserver_py3/bin/python
# -*- coding:utf-8 -*-

import os
import multiprocessing

# 绑定ip和端口号
bind = '0.0.0.0:5556'

# 监听队列
backlog = 512

# 设置超时时间120s，默认为30s。按自己的需求进行设置timeout = 120
timeout = 120

# 超时重启
graceful_timeout = 300

# 在keep-alive连接上等待请求的秒数，默认情况下值为2。一般设定在1~5秒之间。
keepalive = 3

# HTTP请求行的最大大小，此参数用于限制HTTP请求行的允许大小，默认情况下，这个值为4094。
# 值是0~8190的数字。此参数可以防止任何DDOS攻击
limit_request_line = 5120

# 限制HTTP请求中请求头字段的数量。
# 此字段用于限制请求头字段的数量以防止DDOS攻击，与 limit-request-field-size 一起使用可以提高安全性。
# 默认情况下，这个值为100，这个值不能超过32768
limit_request_fields = 101

# 限制HTTP请求中请求头的大小，默认情况下这个值为8190。
# 值是一个整数或者0，当该值为0时，表示将对请求头大小不做限制
limit_request_field_size = 8190

# 设置gunicorn使用的python虚拟环境
pythonpath = '/data/software/jumpserver_py3/bin/python'

# 环境变量
raw_env = 'APE_API_ENV=DEV'

# gunicorn要切换到的目的工作目录
chdir = '/data/software/game_ops_server'

# 使用gevent模式，还可以使用sync 模式，默认的是sync模式
worker_class = 'sync'

# 并行工作进程数, int，cpu数量*2+1 推荐进程数
workers = multiprocessing.cpu_count() * 2 + 1
threads = 1000  # 指定每个进程开启的线程数

# 设置最大并发量（每个worker处理请求的工作线程数，正整数，默认为1）
worker_connections = 2000

# 最大客户端并发数量，默认情况下这个值为1000。此设置将影响gevent和eventlet工作模式
max_requests = 2000

# 设置进程文件目录
pidfile = '/run/game_ops_server.pid'

loglevel = 'error'  # 日志级别，这个日志级别指的是错误日志的级别，而访问日志的级别无法设置

# 设置gunicorn访问日志格式，错误日志无法设置
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'

# 创建日志目录
os.makedirs('logs', mode=0o755, exist_ok=True)
# 设置访问日志和错误信息日志路径
accesslog = "logs/gunicorn_server_info_access.log"  # 访问日志文件
errorlog = "logs/gunicorn_server_info_error.log"  # 错误日志文件

# 进程名
proc_name = 'gunicorn_process'

# 关键：预加载应用，确保JWT密钥全局一致
preload_app = True

"""
其每个选项的含义如下：
h          remote address
l          '-'
u          currently '-', may be user name in future releases
t          date of the request
r          status line (e.g. ``GET / HTTP/1.1``)
s          status
b          response length or '-'
f          referer
a          user agent
T          request time in seconds
D          request time in microseconds
L          request time in decimal seconds
p          process ID
"""
