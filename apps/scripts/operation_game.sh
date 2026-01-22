#!/usr/bin/env bash
# shellcheck disable=SC2016,SC1079,SC2154,SC2143,SC1078,SC2181

#################################################################
#
# 用途: 运维平台调用脚本操作游戏服
#
# 日期: 2025-11-20
#
# 作者: moyuanbo@yeah.net
#
#################################################################

# 渠道
channel_name=$1
# IP
game_ip=$2
# ssh端口
ssh_port=22

if [[ $# == 4 && "$3" == "rsync" ]]; then
    parameter=$3
    package_file=$4
else
    # game目录
    game_dir=$3
    # 游戏服操作参数
    parameter=$4
    # 游戏服主目录
    game_home=/data/gameserver
fi

# 获取执行代码的目录路径
bash_dir=$(pwd)
# 执行日志存放路径
script_name=$(echo $0 | awk -F'/' '{print $NF}' | awk -F'.' '{print $1}')
log_dir=${bash_dir}/logs
execute_log=${log_dir}/${script_name}_server_$(date +"%Y%m%d").log

function current_time() {
    date +"%Y%m%d %H:%M:%S"
}

function echo_error() {
    echo -e "\e[31;1m[$(current_time)] ${1}\e[0m" | tee -a $execute_log
}

function echo_succes() {
    echo -e "\e[32;1m[$(current_time)] ${1}\e[0m" | tee -a $execute_log
}

function echo_print() {
    echo -e "\e[33;1m[$(current_time)] ${1}\e[0m" | tee -a ${execute_log}
}

function judge_exit() {
    if [[ $? -eq 0 ]]; then
        echo_succes "\e[33;1m[成功]\e[32;1m ${1}"
    else
        error_exit "\e[33;1m[失败]\e[31;1m ${1}"
    fi
}

function error_exit() {
    echo_error "${1}"
    exit 1
}

#ssh变量
chmod 400 jump_server
ssh_parameter='-o MACs=umac-64@openssh.com -o StrictHostKeyChecking=no -o GSSAPIAuthentication=no -i jump_server'
SSH="ssh $ssh_parameter -p${ssh_port}"
# scp限速10m传输
SCP="scp $ssh_parameter -l 100000 -P${ssh_port}"
# 时间日志命名
time_file=$(date +'%Y%m%d_%H%M%S')

game_route=$game_home/$channel_name/$game_dir

if [[ "$parameter" == 'stop' || "$parameter" == 'start' ]]; then
    $SSH root@$game_ip "cd $game_route && sh run.sh $parameter"

elif [[ "$parameter" == 'rsync' ]]; then
    echo_print "包体文件为: $package_file"
    if [[ $(echo $package_file | grep -w 'codeUpdate') ]]; then
        rsync_mode='更新包'
        package_dir=bin
    elif [[ $(echo $package_file | grep -w 'hotUpdate') ]]; then
        rsync_mode='热更包'
        package_dir=newfile
    elif [[ $(echo $package_file | grep -w 'battleReportUpdate') ]]; then
        rsync_mode='录像包'
        package_dir=tryOut
    else
        error_exit "无法识别包体文件信息"
    fi

    # 按压缩格式进行解压
    tar_file=$(echo $package_file | awk -F'/' '{print $NF}')
    if [[ $(echo $tar_file | grep -E '\.tar\.gz$') ]]; then
        tar_cmd="tar zxf ${channel_name}_$tar_file -C /data/package_game/${channel_name}_$package_dir/"
    elif [[ $(echo $tar_file | grep -E '\.zip$') ]]; then
        tar_cmd="unzip -q ${channel_name}_$tar_file -d /data/package_game/${channel_name}_$package_dir/"
    elif [[ $(echo $tar_file | grep -E '\.tar$') ]]; then
        tar_cmd="tar -xf ${channel_name}_$tar_file -C /data/package_game/${channel_name}_$package_dir/"
    else
        error_exit "无法识别压缩包信息"
    fi

    # 按渠道进行重命名和渠道目录进行隔离
    $SSH root@$game_ip "[[ -d /data/package_game ]] || mkdir -p /data/package_game"
    $SSH root@$game_ip "[[ -d /data/package_game/${channel_name}_$package_dir ]] && \
        mv /data/package_game/${channel_name}_$package_dir /data/package_game/${channel_name}_${package_dir}_$time_file"
    $SSH root@$game_ip "[[ -d /data/package_game/${channel_name}_$package_dir ]] && error_exit '旧代码重命名失败'"
    $SCP $package_file root@$game_ip:/data/package_game/${channel_name}_$tar_file
    judge_exit "服务器($game_ip) ${rsync_mode}($package_dir)同步"

    $SSH root@$game_ip "mkdir -p /data/package_game/${channel_name}_$package_dir"
    $SSH root@$game_ip "cd /data/package_game/ && $tar_cmd"
    judge_exit "服务器($game_ip) ${rsync_mode}($package_dir)解压"

elif [[ "$parameter" == 'update' ]]; then
    $SSH root@$game_ip "[[ -d /data/backup_game ]] || mkdir -p /data/backup_game"
    $SSH root@$game_ip "ls $game_route/bin &> /dev/null"
    if [[ $? -eq 0 ]]; then
        $SSH root@$game_ip "cp -r $game_route/bin /data/backup_game/${channel_name}_${game_dir}_$time_file"
        judge_exit "渠道($channel_name) 区服($game_dir) 服务器($game_ip) 旧代码备份完成" $game_log_file
    fi

    echo_print "更新来源代码目录: /data/package_game/${channel_name}_bin/bin/"
    # 用rsync同步，限制传输速度为10M每秒，防止IO过载
    $SSH root@$game_ip "rsync -avz --delete -P --bwlimit=10M /data/package_game/${channel_name}_bin/bin/ $game_route/bin/ &> /dev/null"
    judge_exit "渠道($channel_name) 区服($game_dir) 服务器($game_ip) 代码更新完成"

elif [[ "$parameter" == 'reload' ]]; then
    $SSH root@$game_ip "[[ -d /data/backup_game ]] || mkdir -p /data/backup_game"
    $SSH root@$game_ip "ls $game_route/hotswap/newfile &> /dev/null"
    if [[ $? -eq 0 ]]; then
        $SSH root@$game_ip "cp -r $game_route/hotswap/newfile /data/backup_game/${channel_name}_${game_dir}_hotswap_$time_file"
        judge_exit "渠道($channel_name) 区服($game_dir) 服务器($game_ip) 热更旧代码备份完成" $game_log_file
    else
        $SSH root@$game_ip "mkdir -p $game_route_dir/hotswap/newfile"
    fi

    echo_print "热更来源代码目录: /data/package_game/${channel_name}_newfile/newfile/"
    # 用rsync同步，限制传输速度为10M每秒，防止IO过载
    $SSH root@$game_ip "rsync -avz --delete -P --bwlimit=10M /data/package_game/${channel_name}_newfile/newfile/ $game_route/hotswap/newfile/ &> /dev/null"
    judge_exit "渠道($channel_name) 区服($game_dir) 服务器($game_ip) 代码更新完成"
    $SSH root@$game_ip '''cd /data/package_game/'${channel_name}'_newfile/newfile/ && \
        if [[ -f "info.txt" ]]; then \
            for i in $(find ./ ! -name "*.txt" -name "*.class"); do \
                file_name=$(echo "$i" | sed -r "s#\./##"); \
                if ls "$file_name" &> /dev/null; then \
                    cp "$file_name" '${game_route}'/bin/"$file_name" && \
                    echo "文件($file_name)同步完成" || echo "文件($file_name)同步失败"; \
                else \
                    echo "文件($file_name)不存在，同步未成功"; \
                fi; \
            done; \
        else \
            echo "info.txt文件不存在，终止同步"; \
        fi'''
elif [[ "$parameter" == 'battle' ]]; then
    $SSH root@$game_ip "[[ -d /data/backup_game ]] || mkdir -p /data/backup_game"
    $SSH root@$game_ip "ls $game_route/battleReport/tryOut &> /dev/null"
    if [[ $? -eq 0 ]]; then
        $SSH root@$game_ip "cp -r $game_route/battleReport/tryOut /data/backup_game/${channel_name}_${game_dir}_tryOut_$time_file"
        judge_exit "渠道($channel_name) 区服($game_dir) 服务器($game_ip) 录像备份完成" $game_log_file
    fi

    echo_print "更新来源代码目录: /data/package_game/${channel_name}_tryOut/tryOut/"
    # 用rsync同步，限制传输速度为10M每秒，防止IO过载
    $SSH root@$game_ip "rsync -avz -P --bwlimit=10M /data/package_game/${channel_name}_tryOut/tryOut/ $game_route/battleReport/tryOut/ &> /dev/null"
    judge_exit "渠道($channel_name) 区服($game_dir) 服务器($game_ip) 录像更新完成"
fi
