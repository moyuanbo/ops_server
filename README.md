创建数据库: CREATE DATABASE IF NOT EXISTS ops_game DEFAULT CHARSET utf8 COLLATE utf8_general_ci;<br>
部署: 把 ops_game.sql 表 导入数据库中<br> 
创建用户: 把 ops_users.sql 表 导入数据库中<br> 
python版本要求 >= 3.10<br> 
安装模块: pip install -r requirements.txt<br>
安装supervisor: yum -y install supervisor<br>
配置管理: vim /etc/supervisord.d/ops_game.ini<br>
```angular2html
; 项目名
[program:ops_game]
; 项目目录
directory=/data/software/game_ops_server
 
;main:指的是main.py代码文件，app指的是app = Flask(__name__)
command=/data/software/jumpserver_py3/bin/gunicorn -c gunicorn_server_info.py run:app
 
; supervisor启动的时候是否随着同时启动，默认True
autostart=true
autorestart=false
 
; 这个选项是子进程启动多少秒之后，此时状态如果是 running，则我们认为启动成功了。默认值为1
startsecs=1
 
; 当进程启动失败后，最大尝试的次数。当超过5次后，进程的状态变为FAIL
startretries=5
 
; 这个东西主要用于，supervisord管理的子进程，这个子进程本身还有子进程。那么我们如果仅仅干掉supervisord的子进程的话，子进程的子进程有可能会变成孤儿进程。所以可以设置这个选项，把整个该子进程的整个进程组干掉。默认false
stopasgroup=true
 
; 程序运行的用户身份
user = root
 
# 日志输出
stdout_logfile=/data/logs/supervisor/%(program_name)s_out.log
 
#把stderr重定向到stdout，默认 false
redirect_stderr = true
 
#stdout日志文件大小，默认 50MB
stdout_logfile_maxbytes = 100MB
 
#stdout日志文件备份数
stdout_logfile_backups = 20
```

更新supervisor配置: supervisorctl update<br> 

登录链接: http://IP:5556<br>
登录账号密码信息:<br> 
Username: admin<br> 
Password: Admin@123<br> 
