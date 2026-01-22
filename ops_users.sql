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

 Date: 16/12/2025 10:50:55
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

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
-- Records of ops_users
-- ----------------------------
INSERT INTO `ops_users` VALUES (1, 'admin', '管理员', 'admin@example.com', 'scrypt:32768:8:1$3ss7addBZmIdWDCo$0a3d320c017581ed8e1c596e456276fb25af1fae68456cffe5f7d1d336dc94e73a995bc41f66f6b66a0592e2ac33de26fd27e22768a096b09c46f31ff693faf8', 1, '2025-11-25 02:50:32', '2025-12-15 15:06:21', '2025-12-16 02:49:37', 0, 0, 0, 'scrypt');

SET FOREIGN_KEY_CHECKS = 1;
