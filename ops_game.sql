/*
 Navicat Premium Data Transfer

 Source Server         : 本地运维
 Source Server Type    : MySQL
 Source Server Version : 80021
 Source Host           : 172.10.10.3:3306
 Source Schema         : ops_game

 Target Server Type    : MySQL
 Target Server Version : 80021
 File Encoding         : 65001

 Date: 16/12/2025 10:44:01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for channel_list
-- ----------------------------
DROP TABLE IF EXISTS `channel_list`;
CREATE TABLE `channel_list`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `channel_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '渠道名称',
  `annotation` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '用来打印的',
  `alias_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '中文名称',
  `initial_id` int(0) NOT NULL COMMENT '渠道的游戏服初始id',
  `external_switch` int(0) NOT NULL DEFAULT 0 COMMENT '0为内网，1为外网；默认为内网(0)',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_server_list
-- ----------------------------
DROP TABLE IF EXISTS `game_server_list`;
CREATE TABLE `game_server_list`  (
  `id` int(0) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '游戏服列表',
  `channel_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '渠道简称',
  `server_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '区服类型',
  `server_dir` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '区服目录',
  `game_nu` int(0) NOT NULL COMMENT '区服number',
  `external_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '外网IP',
  `intranet_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '内网IP',
  `server_db_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '游戏服数据库IP地址',
  `server_db_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '游戏服库名',
  `open_status` int(0) NOT NULL DEFAULT 0 COMMENT '开服状态:0(未开服)1(已开服)',
  `game_status` int(0) NOT NULL DEFAULT 0 COMMENT '游戏服状态:0(正式服)1(测试服)2(已删除)3(未定义)',
  `http_port` int(0) NOT NULL DEFAULT 0 COMMENT '后台http端口',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 52 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for game_type_list
-- ----------------------------
DROP TABLE IF EXISTS `game_type_list`;
CREATE TABLE `game_type_list`  (
  `id` int(0) NOT NULL,
  `server_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '游戏服类型',
  `annotation` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '用来打印的',
  `alias_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '中文名称',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for m_serverinfo
-- ----------------------------
DROP TABLE IF EXISTS `m_serverinfo`;
CREATE TABLE `m_serverinfo`  (
  `id` bigint(0) NOT NULL AUTO_INCREMENT COMMENT '唯一id',
  `zoneid` int(0) NULL DEFAULT NULL COMMENT '区号',
  `alias` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '区服名',
  `pf` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '平台号',
  `port` int(0) NULL DEFAULT NULL COMMENT '端口',
  `houtaiport` int(0) NULL DEFAULT NULL COMMENT '后台端口',
  `rechargeport` int(0) NULL DEFAULT NULL COMMENT '充值端口',
  `ip` varchar(250) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT 'ip地址',
  `state` int(0) NULL DEFAULT NULL COMMENT '区服状态 0待开服（白名单可见），1:已开服，2维护，3关服',
  `dbip` varchar(250) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '数据库ip',
  `dbport` int(0) NULL DEFAULT NULL COMMENT '数据库端口',
  `dbname` varchar(250) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '数据库名称',
  `dbuser` varchar(250) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '数据库user',
  `dbpwd` varchar(250) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '数据库密码',
  `masterZone` int(0) NULL DEFAULT NULL COMMENT '主区区号',
  `onlineStatus` int(0) NULL DEFAULT NULL COMMENT '区服承载： （1）火爆、（2）流畅、（3）拥挤',
  `opentime` int(0) NULL DEFAULT NULL COMMENT '实际开服时间 时间戳',
  `autoopen` int(0) NULL DEFAULT NULL COMMENT '自动开服标志',
  `content` varchar(500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '维护公告',
  `hefuServer` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '合服区',
  `hefuTime` int(0) NULL DEFAULT NULL COMMENT '合服时间',
  `clientversion` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '客户端版本',
  `resversion` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '客户端资源版本',
  `clienturl` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '客户端请求url',
  `clienturl2` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '客户端请求url2',
  `bigZoneId` int(0) NULL DEFAULT NULL COMMENT '大区id',
  `appIdCchIds` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '渠道标识唯一id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `i_zoneid`(`zoneid`) USING BTREE,
  INDEX `i_pf`(`pf`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9006 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for mysql_list
-- ----------------------------
DROP TABLE IF EXISTS `mysql_list`;
CREATE TABLE `mysql_list`  (
  `id` int(0) UNSIGNED NOT NULL AUTO_INCREMENT,
  `host_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '主机名',
  `alias_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '主机名称/主机备注(简称)',
  `intranet_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '内网IP地址',
  `belong_to_channel` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '该服务器归属哪些渠道的，可以多个渠道一起使用这台服务器，从channel_list列表选择',
  `server_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '服务器用途/服务器类型，从game_type_list列表选择',
  `opening_up` int(0) NOT NULL DEFAULT 1 COMMENT '服务器使用状态(1:正常,2:不可用,3:已退订)',
  `mysql_port` int(0) NOT NULL COMMENT 'MySQL服务端口',
  `cpu_info` int(0) NOT NULL COMMENT 'CPU核数',
  `men_info` int(0) NOT NULL COMMENT '内存/G',
  `hard_disk` int(0) NOT NULL COMMENT '硬盘/G',
  `system_info` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '服务器系统信息',
  `external_switch` int(0) NOT NULL DEFAULT 0 COMMENT '0为内网，1为外网；默认为内网(0)；对应jumpserver的连接方式',
  `tunnel_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '当MySQL不跟运维机同一局域网是的转发IP地址',
  `tunnel_port` int(0) NOT NULL DEFAULT 0 COMMENT '当MySQL不跟运维机同一局域网是的转发端口',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 14 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for number_data
-- ----------------------------
DROP TABLE IF EXISTS `number_data`;
CREATE TABLE `number_data`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `full_number` int(0) NOT NULL,
  `created_at` timestamp(0) NULL DEFAULT CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for operation_game_list
-- ----------------------------
DROP TABLE IF EXISTS `operation_game_list`;
CREATE TABLE `operation_game_list`  (
  `id` int(0) NOT NULL COMMENT 'id',
  `operation_game_list` text CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '要操作的游戏服列表',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for ops_users
-- ----------------------------
DROP TABLE IF EXISTS `ops_users`;
CREATE TABLE `ops_users`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `username` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `real_name` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `email` varchar(120) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `password_hash` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `is_admin` tinyint(1) NULL DEFAULT NULL,
  `created_at` datetime(0) NULL DEFAULT NULL,
  `last_login` datetime(0) NULL DEFAULT NULL,
  `password_changed_at` datetime(0) NULL DEFAULT NULL,
  `failed_login_attempts` int(0) NULL DEFAULT 0,
  `account_locked` tinyint(1) NULL DEFAULT NULL,
  `is_deleted` tinyint(1) NULL DEFAULT NULL,
  `hash_algorithm` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT 'pbkdf2:sha256',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username`) USING BTREE,
  UNIQUE INDEX `email`(`email`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 15 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for reload_url_list
-- ----------------------------
DROP TABLE IF EXISTS `reload_url_list`;
CREATE TABLE `reload_url_list`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `reload_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '热更类型',
  `reload_url` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '热更链接',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for server_list
-- ----------------------------
DROP TABLE IF EXISTS `server_list`;
CREATE TABLE `server_list`  (
  `id` int(0) UNSIGNED NOT NULL AUTO_INCREMENT,
  `host_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '主机名',
  `alias_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '主机名称/主机备注(简称)',
  `external_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '外网IP地址',
  `intranet_ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '内网IP地址',
  `belong_to_channel` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '该服务器归属哪些渠道的，可以多个渠道一起使用这台服务器，从channel_list列表选择',
  `server_type` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '服务器用途/服务器类型，从game_type_list列表选择',
  `opening_up` int(0) NOT NULL DEFAULT 1 COMMENT '服务器使用状态(1:正常,2:不可用,3:已退订)',
  `ssh_port` int(0) NOT NULL COMMENT 'ssh服务端口',
  `cpu_info` int(0) NOT NULL COMMENT 'CPU核数',
  `men_info` int(0) NOT NULL COMMENT '内存/G',
  `hard_disk` int(0) NOT NULL COMMENT '硬盘/G',
  `system_info` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL COMMENT '服务器系统信息',
  `external_switch` int(0) NOT NULL DEFAULT 0 COMMENT '0为内网，1为外网；默认为内网(0)；对应jumpserver的连接方式',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 18 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for time_zone_test
-- ----------------------------
DROP TABLE IF EXISTS `time_zone_test`;
CREATE TABLE `time_zone_test`  (
  `id` int(0) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '自增主键',
  `dt_col` datetime(0) NULL DEFAULT NULL COMMENT 'datetime时间',
  `ts_col` timestamp(0) NULL DEFAULT NULL COMMENT 'timestamp时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = 'time_zone测试表' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
