#!/usr/bin/env bash
# shellcheck disable=SC2034,SC2209,SC2154,SC2181,SC2219,SC2115

#################################################################
#
# 用途: 运维平台调用脚本部署游戏服
#
# 日期: 2025-12-17
#
# 作者: moyuanbo@yeah.net
#
#################################################################

# 加载环境变量，防止MySQL环境获取不到
source /etc/profile

# 渠道
channel_name=$1
# IP
game_ip=$2
# 区服类型
game_type=$3
# 区服目录
game_dir=$4
# 区服number
game_nu=$5
# svn更新锁
svn_lock=$6
# 游戏服操作参数
parameter=$7

# ==================================== 常规变量 ====================================
# ssh端口
ssh_port=22
# 设置权限，防止权限过大，导致连不上
chmod 400 jump_server
ssh_parameter='-o MACs=umac-64@openssh.com -o StrictHostKeyChecking=no -o GSSAPIAuthentication=no -i jump_server'
SSH="ssh $ssh_parameter -p${ssh_port}"
# scp限速10m传输
SCP="scp $ssh_parameter -l 100000 -P${ssh_port}"

# 游戏服主目录
game_home=/data/gameserver
# 游戏服渠道目录配置路径
game_route_dir=$game_home/$channel_name

# 获取执行代码的目录路径
bash_dir=$(pwd)

# 执行日志存放路径
script_name=$(echo $0 | awk -F'/' '{print $NF}' | awk -F'.' '{print $1}')
log_dir=${bash_dir}/logs
execute_log=${log_dir}/${script_name}_server_$(date +"%Y%m%d").log

# 月份记录
declare -A month_list
month_list[Jan]=1
month_list[Feb]=2
month_list[Mar]=3
month_list[Apr]=4
month_list[May]=5
month_list[Jun]=6
month_list[Jul]=7
month_list[Aug]=8
month_list[Sept]=9
month_list[Oct]=10
month_list[Nov]=11
month_list[Dec]=12

# 游戏服列表
server_game_table='m_serverinfo'  # 单服表

# 运维数据库信息
ops_user=write
ops_ip=172.10.10.3
ops_port=3306
ops_pass='123456'
ops_db='ops_game'
ops_game_table='game_server_list'
ops_channel_table='channel_list'
ops_mysql_list='mysql_list'
game_list_table='game_server_list'

# 游戏服数据库账号密码
game_my_user=write
game_my_pass='123456'
game_read_user=readonly_sh_dev
game_read_pass='Mssql@e8aX&Nxtz1'

# 后台数据库账号密码
background_user=write
background_pass='123456'
background_db='sh-admin'
background_table='sh_group'

# 游戏服数据库链接
game_mysql_com="mysql -u${game_my_user}"
# 运维服数据库链接
ops_mysql_com="mysql -u${ops_user} -h$ops_ip -P$ops_port $ops_db"
# 后台服数据库链接
background_com="mysql -u${background_user}"

# svn信息
svn_user=yunwei
svn_passwd=Ff6JLjPNSG
svn_com="svn --username=${svn_user} --password=${svn_passwd} --no-auth-cache"
svn_url=http://yunwei.hongtu.com/svn/yunwei
# SVN更新目录
svn_dir=${bash_dir}/svn_game_update
# 游戏服svn信息
game_svn=http://yunwei.hongtu.com/svn/game_info
game_svn_dir=/data/common/ops/game_info

# 做随机颜色变量
colour_list=(30 31 32 33 34 35 36 37 38)
lang_num=${#colour_list[*]}

# ==================================================================================

function current_time() {
    date +"%Y%m%d %H:%M:%S"
}

function echo_error() {
    echo -e "\e[31;1m[$(current_time)] ${1}\e[0m" | tee -a ${execute_log}
}

function echo_succes() {
    echo -e "\e[32;1m[$(current_time)] ${1}\e[0m" &>> ${execute_log}
}

function echo_print() {
    echo -e "\e[33;1m[$(current_time)] ${1}\e[0m" | tee -a ${execute_log}
}

function judge_exit() {
    if [[ $? -eq 0 ]]; then
        echo_succes "\e[33;1m[成功]\e[32;1m ${1}"
    else
        echo_error "\e[33;1m[失败]\e[31;1m ${1}"
        exit 1
    fi
}

function error_exit() {
    echo_error "${1}"
    exit 1
}

function initial_game() {
    # 获取游戏服信息
    export MYSQL_PWD=$ops_pass
    game_info=$($ops_mysql_com -N -e "SELECT external_ip, intranet_ip, server_db_ip, server_db_name, http_port FROM \
                $ops_game_table WHERE \
                channel_name = '$channel_name' AND server_type = '$game_type' AND game_nu = $game_nu")
    judge_exit "获取游戏服信息"
    # 游戏服服务器外网IP
    external_ip=$(echo $game_info | awk '{print $1}')
    # 游戏服服务器内网IP
    intranet_ip=$(echo $game_info | awk '{print $2}')
    # 游戏服数据库IP
    server_db_ip=$(echo $game_info | awk '{print $3}')
    # 游戏服库名
    server_db_name=$(echo $game_info | awk '{print $4}')
    # 游戏服HttpPort端口
    http_port=$(echo $game_info | awk '{print $5}')

    # 获取游戏服数据库信息
    mysql_info=$($ops_mysql_com -N -e "SELECT tunnel_ip, tunnel_port, background_tunnel_mysql FROM $ops_mysql_list \
                 WHERE belong_to_channel='$channel_name' ORDER BY id DESC LIMIT 1")
    judge_exit "获取游戏服数据库信息"
    game_db_ip=$(echo $mysql_info | awk '{print $1}')
    game_db_port=$(echo $mysql_info | awk '{print $2}')
    background_tunnel_mysql=$(echo $mysql_info | awk '{print $3}')

    # 获取渠道信息
    channel_info=$($ops_mysql_com -N -e "SELECT initial_id, external_switch, game_initial_port, game_id, platform,
                   ui_title, central_port_1, global_ip, global_port, global_zone_id, play1_zone_id, play2_zone_id,
                   play_init_port, central_zone_id, central_port, recharge_port, client_http_port, sdk_port, nginx_dir,
                   nginx_ip, nginx_bin, domain_name, api_server_port, nginx_init_port, nginx_central_client,
                   nginx_central_sdk, nginx_central_http, nginx_central_recharge, sdk_platform_id, sdk_platform,
                   cdkey_url, background_mysql_ip, background_mysql_port FROM
                   $ops_channel_table WHERE channel_name='$channel_name'")
    judge_exit "获取渠道信息"

    # 游戏服初始id
    initial_id=$(echo $channel_info | awk '{print $1}')
    # 跟运维机是否同一个局域网，0为是，1为不是
    external_switch=$(echo $channel_info | awk '{print $2}')
    # 游戏服的初始端口
    game_initial_port=$(echo $channel_info | awk '{print $3}')
    # 平台分配的id
    game_id=$(echo $channel_info | awk '{print $4}')
    # 区服配置文件的平台名称
    platform=$(echo $channel_info | awk '{print $5}')
    # UI标题
    ui_title=$(echo $channel_info | awk '{print $6}')
    # 后台中央服 端口
    central_port_1=$(echo $channel_info | awk '{print $7}')
    # 世界服IP地址
    global_ip=$(echo $channel_info | awk '{print $8}')
    # 世界服端口
    global_port=$(echo $channel_info | awk '{print $9}')
    # 世界服zone id
    global_zone_id=$(echo $channel_info | awk '{print $10}')
    # 玩法服1的zone id
    play1_zone_id=$(echo $channel_info | awk '{print $11}')
    # 玩法服2的zone id
    play2_zone_id=$(echo $channel_info | awk '{print $12}')
    # 玩法服初始端口
    play_init_port=$(echo $channel_info | awk '{print $13}')
    # 中心服zone id
    central_zone_id=$(echo $channel_info | awk '{print $14}')
    # 中心服端口,对应serverPort
    central_port=$(echo $channel_info | awk '{print $15}')
    # 中心服充值端口
    recharge_port=$(echo $channel_info | awk '{print $16}')
    # 中心服前端端口
    client_http_port=$(echo $channel_info | awk '{print $17}')
    # 中心服sdk端口
    sdk_port=$(echo $channel_info | awk '{print $18}')
    # nginx配置目录
    nginx_dir=$(echo $channel_info | awk '{print $19}')
    # nginx服务器IP地址
    nginx_ip=$(echo $channel_info | awk '{print $20}')
    # nginx命令路径
    nginx_bin=$(echo $channel_info | awk '{print $21}')
    # 游戏服域名
    domain_name=$(echo $channel_info | awk '{print $22}')
    # 游戏服列表转发端口
    api_server_port=$(echo $channel_info | awk '{print $23}')
    # 游戏服转发到外网的初始端口
    nginx_init_port=$(echo $channel_info | awk '{print $24}')
    # 中心服client_http端口转发外网端口
    nginx_central_client=$(echo $channel_info | awk '{print $25}')
    # 中心服sdkPort转发外网端口
    nginx_central_sdk=$(echo $channel_info | awk '{print $26}')
    # 中心服HttpPort转发外网端口
    nginx_central_http=$(echo $channel_info | awk '{print $27}')
    # 中心服rechargePort转发外网端口
    nginx_central_recharge=$(echo $channel_info | awk '{print $28}')
    # config/sdk.properties
    sdk_platform_id=$(echo $channel_info | awk '{print $29}')
    # config/sdk.properties
    sdk_platform=$(echo $channel_info | awk '{print $30}')
    # 中心服游戏服列表接口URL
    cdkey_url=$(echo $channel_info | awk '{print $31}')
    # 后台MySQL IP地址
    background_mysql_ip=$(echo $channel_info | awk '{print $32}')
    # 后台MySQL端口
    background_mysql_port=$(echo $channel_info | awk '{print $33}')

    # 获取中心服信息
    central_info=$($ops_mysql_com -N -e "SELECT intranet_ip, server_db_ip, server_db_name \
                 FROM $game_list_table WHERE \
                 channel_name='$channel_name' AND server_type='Central'")
    judge_exit "获取中心服信息"
    central_ip=$(echo $central_info | awk '{print $1}')
    central_db_ip=$(echo $central_info | awk '{print $2}')
    central_db_name=$(echo $central_info | awk '{print $3}')
    if [[ "$central_db_ip" == "$game_db_ip" ]]; then
        central_db_port=$game_db_port
    else
        central_db_info=$($ops_mysql_com -N -e "SELECT tunnel_ip, tunnel_port FROM $ops_mysql_list \
                         WHERE intranet_ip='$central_db_ip' ORDER BY id DESC LIMIT 1")
        judge_exit "获取中心服数据库信息"
        central_db_ip=$(echo $central_db_info | awk '{print $1}')
        central_db_port=$(echo $central_db_info | awk '{print $2}')
    fi

    # 先检查相关的区服信息
    [[ -d ${bash_dir}/$game_dir ]] && error_exit "运维机上，游戏服($game_dir)目录已存在"
    $SSH root@$game_ip "ls $game_route_dir/$game_dir &> /dev/null"
    [[ $? -eq 0 ]] && error_exit "游戏服($game_dir)在服务器($game_ip)上目录已存在"
    # 查看数据库是否存在
    export MYSQL_PWD=$game_my_pass
    $game_mysql_com -P$game_db_port -h$game_db_ip -N -e "SHOW DATABASES;" | grep "^${server_db_name}$" &> /dev/null
    [[ $? -eq 0 ]] && error_exit "游戏服($server_db_name)数据库已存在"

    # 区服类型对应的区服信息
    if [[ "$game_type" == "Game" ]]; then
        # zone_id
        let zone_id=${initial_id}+${game_nu}
        # 对应serverPort端口
        let game_port=${game_initial_port}+${game_nu}
        # 区服配置
        game_config=game.properties
        # nginx转发端口
        let nginx_game_port=${nginx_init_port}+${game_nu}
    elif [[ "$game_type" == "Global" ]]; then
        zone_id=$global_zone_id
        game_port=$global_port
        game_config=gameGlobal.properties
    elif [[ "$game_type" == "Play" ]]; then
        if [[ $game_nu -eq 1 ]]; then
            zone_id=$play1_zone_id
        elif [[ $game_nu -eq 2 ]]; then
            zone_id=$play2_zone_id
        else
            error_exit "获取不到play类型 ${game_nu}服的zone_id"
        fi
        let game_port=${play_init_port}+${game_nu}
        game_config=gamePlay.properties
    elif [[ "$game_type" == "Central" ]]; then
        zone_id=$central_zone_id
        game_port=$central_port
        game_config=gameCentral.properties
    fi

    # 检查端口
    if [[ "$game_type" == "Game" ]]; then
        $SSH root@$game_ip "ss -untpl | grep -E ':${game_port} '"
        [[ $? -eq 0 ]] && error_exit "区服($game_dir)的端口($game_port)在服务器($game_ip)有服务在使用"

    elif [[ "$game_type" == "Global" ]]; then
        $SSH root@$game_ip "ss -untpl | grep -E ':${game_port} |:${http_port} '"
        [[ $? -eq 0 ]] && error_exit "区服($game_dir)的端口($game_port)在服务器($game_ip)有服务在使用"

    elif [[ "$game_type" == "Play" ]]; then
        $SSH root@$game_ip "ss -untpl | grep -E ':${game_port} |:${http_port} '"

    elif [[ "$game_type" == "Central" ]]; then
        $SSH root@$game_ip "ss -untpl | grep -E ':${game_port} |:${http_port} |:${recharge_port} |:${client_http_port} |:${sdk_port} |:${central_port_1} '"
        [[ $? -eq 0 ]] && error_exit "区服($game_dir)的端口($game_port)在服务器($game_ip)有服务在使用"

    fi

    if [[ "$svn_lock" == 'no_lock' ]]; then
        # 先查看SVN库上有没有这个路径库
        $svn_com info $game_svn &> /dev/null
        [[ $? -ne 0 ]] && error_exit "svn路径错误或者是SVN用户($svn_user)没有权限去拉取SVN库:${game_svn},请检查"
        [[ -d $game_svn_dir ]] || mkdir -p $game_svn_dir
        if [[ -d  ${game_svn_dir}/.svn ]];then
            echo_print "正在更新SVN资源($game_svn_dir)，请等待........."
            $svn_com cleanup $game_svn_dir &> $execute_log && $svn_com up $game_svn_dir &> $execute_log
            judge_exit "svn up $game_svn_dir 资源更新"
        else
            echo_succes "正在检出SVN资源($game_svn_dir)，请等待........."
            $svn_com co $game_svn $game_svn_dir &> /dev/null
            judge_exit "svn co $game_svn $game_svn_dir 资源检出"
        fi
    
        # 先查看SVN库上有没有这个路径库
        $svn_com info $svn_url &> /dev/null
        [[ $? -ne 0 ]] && error_exit "svn路径错误或者是SVN用户($svn_user)没有权限去拉取SVN库:${svn_url},请检查"
        [[ -d $svn_dir ]] || mkdir -p $svn_dir
        if [[ -d  ${svn_dir}/.svn ]];then
            echo_print "正在更新SVN资源($svn_dir)，请等待........."
            $svn_com cleanup $svn_dir &> $execute_log && $svn_com up $svn_dir &> $execute_log
            judge_exit "svn up $svn_dir 资源更新"
        else
            echo_succes "正在检出SVN资源($svn_dir)，请等待........."
            $svn_com co $svn_url $svn_dir &> /dev/null
            judge_exit "svn co $svn_url $svn_dir 资源检出"
        fi
    else
        sleep 10
    fi

    # 渠道对应代码目录
    channel_svn_dir=$svn_dir/$channel_name
    channel_game_svn_dir=$game_svn_dir/$channel_name
    [[ "$channel_name" == "lingjing_weixin" ]] && channel_svn_dir=$svn_dir/weixin
    [[ "$channel_name" == "lingjing_weixin" ]] && channel_game_svn_dir=$game_svn_dir/weixin

    # 复制默认配置
    cp -r ${game_svn_dir}/default_game ${bash_dir}/$game_dir
    judge_exit "游戏服($game_dir)目录复制"
    # 复制渠道的录像文件
    \cp -r $channel_game_svn_dir/tryOut ${bash_dir}/$game_dir/battleReport
    judge_exit "游戏服($game_dir)录像文件复制"
    tar -zxf $channel_svn_dir/codeUpdate/bin.tar.gz -C ${bash_dir}/$game_dir
    judge_exit "解压包体到游戏服($game_dir)目录"
    tar -xf $channel_svn_dir/battleReportUpdate/tryOut.tar -C ${bash_dir}/$game_dir/battleReport
    judge_exit "解压录像到游戏服($game_dir)目录"

    sed -i -e "s/##zone_id##/$zone_id/" \
           -e "s/##db_ip##/$server_db_ip/" \
           -e "s/##db_name##/$server_db_name/" ${bash_dir}/$game_dir/config/dbs.properties
    update_count=$(grep -oE "^$zone_id=|$server_db_ip|$server_db_name" \
        ${bash_dir}/$game_dir/config/dbs.properties | wc -l)
    [[ $update_count -ne 3 ]] && \
        cat ${bash_dir}/$game_dir/config/dbs.properties && \
        error_exit "游戏服($game_dir)修改dbs.properties配置文件数据不对，请查看"

    # 复制配置文件
    \cp -f ${game_svn_dir}/game_config/$game_config ${bash_dir}/$game_dir/config/
    judge_exit "游戏服($game_dir)配置文件复制"

    # 修改配置文件
    open_time=$(date +'%Y-%m-%d')
    sed -i -e "s/##zone_id##/$zone_id/" \
           -e "s/##ip##/$intranet_ip/" \
           -e "s/##game_port##/$game_port/" \
           -e "s/##http_port##/$http_port/" \
           -e "s/##recharge_port##/$recharge_port/" \
           -e "s/##client_port##/$client_http_port/" \
           -e "s/##sdk_port##/$sdk_port/" \
           -e "s/##game_id##/$game_id/" \
           -e "s/##open_time##/$open_time/" \
           -e "s/##platform##/$platform/" \
           -e "s/##ui_title##/$ui_title/" \
           -e "s/##central_ip##/$central_ip/" \
           -e "s/##central_port_1##/$central_port_1/" \
           -e "s/##global_ip##/$global_ip/" \
           -e "s/##global_port##/$global_port/" \
           -e "s/##play1_zone_id##/$play1_zone_id/" \
           -e "s/##cdkey_url##/$cdkey_url/" ${bash_dir}/$game_dir/config/$game_config
    judge_exit "游戏服($game_dir)配置($game_config)修改完成"

    # 修改SDK配置文件
    if [[ "$game_type" == "Game" ]]; then
        \cp -f ${game_svn_dir}/game_config/sdk.properties ${bash_dir}/$game_dir/config/
        judge_exit "游戏服($game_dir)配置(sdk.properties)复制"
        sed -i -e "s/^PLATFORM_ID =.*/PLATFORM_ID = $sdk_platform_id/" \
               -e "s/^PLATFORM =.*/PLATFORM = $sdk_platform/" ${bash_dir}/$game_dir/config/sdk.properties
        judge_exit "游戏服($game_dir)配置(sdk.properties)修改"
    fi

    # 把配置好的区服配置和游戏代码传输到游戏服服务器上
    $SSH root@$game_ip "[[ -d $game_route_dir ]] || mkdir -p $game_route_dir"
    $SCP -r ${bash_dir}/$game_dir root@$game_ip:$game_route_dir &> /dev/null
    judge_exit "游戏服($game_dir)目录传输到服务器($game_ip)"
    $SSH root@$game_ip "touch $game_route_dir/$game_dir/game.lock"
    judge_exit "游戏服($game_dir)创建锁文件"

    # 添加数据库
    $game_mysql_com -P$game_db_port -h$game_db_ip -N -e \
        "CREATE DATABASE IF NOT EXISTS $server_db_name DEFAULT CHARSET utf8 COLLATE utf8_general_ci;"
    judge_exit "游戏服(game_dir)创建数据库($server_db_name)"

    # 写入游戏服列表数据库
    if [[ "$game_type" == "Game" ]]; then
        echo """插入游戏服列表的SQL语句: INSERT INTO ${server_game_table} \
            (id, zoneid, alias, pf, port, houtaiport, rechargeport, ip, state, dbip, dbport, dbname, dbuser, dbpwd, masterZone, \
            onlineStatus, opentime, autoopen, content, hefuServer, hefuTime, clientversion, resversion, clienturl, \
            clienturl2, bigZoneId, appIdCchIds) \
            VALUES \
            ($zone_id, $zone_id, '${ui_title}${game_nu}服', '$platform', $game_port, 0, 0, '$intranet_ip', 0, \
            '$server_db_ip', 3306, '$server_db_name', '$game_my_user', '$game_my_pass', $zone_id, 1, \
            0, 0, '', '', 0, '修改需要等20秒', '修改需要等20秒', \
            'wss://${domain_name}:${nginx_game_port}', 'wss://${domain_name}:${nginx_game_port}', 1, NULL);""" &>> $execute_log
        $game_mysql_com -P$central_db_port -h$central_db_ip $central_db_name -e """INSERT INTO ${server_game_table} \
            (id, zoneid, alias, pf, port, houtaiport, rechargeport, ip, state, dbip, dbport, dbname, dbuser, dbpwd, masterZone, \
            onlineStatus, opentime, autoopen, content, hefuServer, hefuTime, clientversion, resversion, clienturl, \
            clienturl2, bigZoneId, appIdCchIds) \
            VALUES \
            ($zone_id, $zone_id, '${ui_title}${game_nu}服', '$platform', $game_port, 0, 0, '$intranet_ip', 0, \
            '$server_db_ip', 3306, '$server_db_name', '$game_my_user', '$game_my_pass', $zone_id, 1, \
            0, 0, '', '', 0, '修改需要等20秒', '修改需要等20秒', \
            'wss://${domain_name}:${nginx_game_port}', 'wss://${domain_name}:${nginx_game_port}', 1, NULL);"""
        judge_exit "游戏服($game_dir)信息写入游戏服列表数据库"

        # 1. 获取12个月后的日期字符串，用于限制区服开启
        target_date=$(date -d "12 months" "+%Y-%m-%d 00:00:00")
        # 2. 将日期字符串转换为时间戳
        timestamp=$(date -d "$target_date" "+%s")
        echo """插入后台列表的SQL语句: INSERT INTO $background_table \
            (id, sname, code, hot, ip, start_time, status, mysql_ip, mysql_ku, mysql_account, mysql_pwd, \
            auto_register_num, auto_pay_num, is_test) \
            VALUES \
            ($zone_id, '${ui_title}${game_nu}服',  '$platform', 1, 'https://${domain_name}:${nginx_central_http}', \
            $timestamp, 0, '${background_tunnel_mysql}', '${server_db_name}', '${game_read_user}', \
            '${game_read_pass}', 0, 0, 0);""" &>> $execute_log
        export MYSQL_PWD=$background_pass
        $background_com -P$background_mysql_port -h$background_mysql_ip $background_db -e """INSERT INTO \
            $background_table (id, sname, code, hot, ip, start_time, status, mysql_ip, mysql_ku, mysql_account, \
            mysql_pwd, auto_register_num, auto_pay_num, is_test) \
            VALUES \
            ($zone_id, '${ui_title}${game_nu}服',  '$platform', 1, 'https://${domain_name}:${nginx_central_http}', \
            $timestamp, 0, '${background_tunnel_mysql}', '${server_db_name}', '${game_read_user}', \
            '${game_read_pass}', 0, 0, 0);"""
        judge_exit "游戏服($game_dir)信息写入后台列表数据库"
    fi

    # 修改区服状态
    export MYSQL_PWD=$ops_pass
    $ops_mysql_com -e "UPDATE $game_list_table SET game_status = 0 WHERE \
                       channel_name = '$channel_name' AND server_type = '$game_type' \
                       AND server_dir = '$game_dir' AND game_nu = $game_nu;"
    judge_exit "游戏服($game_dir)状态修改"

    [[ -d ${bash_dir}/tmp ]] || mkdir ${bash_dir}/tmp

if [[ "$game_type" == "Game" ]]; then
    if [[ "$channel_name" == 'weixin' ]]; then
cat > ${bash_dir}/tmp/${channel_name}_sh_${game_nu}_${game_port}.conf <<EOF
server {
    listen $nginx_game_port ssl;
    server_name $domain_name;
    
    ssl_certificate /data/gameserver/leniugame.com_bundle.crt;
    ssl_certificate_key /data/gameserver/leniugame.com.key;
    
    location / {
        proxy_pass https://${intranet_ip}:${game_port};
        include /etc/nginx/conf.d/includes/websocket-common.conf;
    }
}
EOF

    else

cat > ${bash_dir}/tmp/${channel_name}_sh_${game_nu}_${game_port}.conf <<EOF
server {
    listen $nginx_game_port ssl;
    server_name $domain_name;

    ssl_certificate /data/apps/nginx/conf/ssl/leniugame.com.crt;
    ssl_certificate_key /data/apps/nginx/conf/ssl/leniugame.com.key;

    location / {
        proxy_pass https://${intranet_ip}:${game_port};

        include /data/apps/nginx/conf/websocket-common.conf;
    }
}
EOF
    fi

    $SCP ${bash_dir}/tmp/${channel_name}_sh_${game_nu}_${game_port}.conf root@$nginx_ip:$nginx_dir/
    judge_exit "游戏服($game_dir)nginx配置同步"
    $SSH root@$nginx_ip "$nginx_bin -t && $nginx_bin -s reload"
    judge_exit "游戏服($game_dir)nginx配置加载"
fi

    # 防止变量没有值导致删错文件的问题
    set -u
    rm -rf ${bash_dir}/$game_dir
    set +u

    echo_print "区服($game_dir)装服完成"
}

if [[ "$parameter" == 'initial' ]]; then
    initial_game
else
    echo "输入的操作参数不对"
fi
