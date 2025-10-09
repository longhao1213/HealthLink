-- ----------------------------
-- 数据库初始化脚本 (v5)
-- ID类型: BIGINT (支持雪花ID)
-- 用户表拆分为 admin_user 和 patient_user
-- 移除外键约束
-- 文件表拆分为 knowledge_file 和 patient_file
-- 为文件表增加详细字段
-- ----------------------------

-- ----------------------------
-- 1. 后台用户表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `admin_user` (
  `id` BIGINT PRIMARY KEY COMMENT '用户ID，雪花ID',
  `username` VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名，用于登录',
  `password` VARCHAR(255) NOT NULL COMMENT '密码',
  `full_name` VARCHAR(255) COMMENT '用户全名',
  `email` VARCHAR(255) UNIQUE COMMENT '电子邮箱',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '账户是否激活',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '后台用户表';

-- ----------------------------
-- 2. 患者用户表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `patient_user` (
  `id` BIGINT PRIMARY KEY COMMENT '患者ID，雪花ID',
  `username` VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名，用于登录',
  `password` VARCHAR(255) NOT NULL COMMENT '密码',
  `phone` VARCHAR(11) NOT NULL COMMENT '手机号',
  `full_name` VARCHAR(255) COMMENT '患者全名',
  `email` VARCHAR(255) UNIQUE COMMENT '电子邮箱',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '账户是否激活',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '患者用户表';

-- ----------------------------
-- 3. 知识库表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `knowledge_base` (
  `id` BIGINT PRIMARY KEY COMMENT '知识库ID，雪花ID',
  `name` VARCHAR(255) NOT NULL COMMENT '知识库名称',
  `description` TEXT COMMENT '知识库描述',
  `admin_user_id` BIGINT COMMENT '创建该知识库的管理员ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '知识库表';

-- ----------------------------
-- 4. 知识库文件表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `knowledge_file` (
  `id` BIGINT PRIMARY KEY COMMENT '文件ID，雪花ID',
  `filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `file_ext` VARCHAR(50) COMMENT '文件扩展名 (e.g., .pdf, .docx)',
  `mime_type` VARCHAR(100) COMMENT '文件的MIME类型 (e.g., application/pdf)',
  `size_in_bytes` BIGINT COMMENT '文件大小（字节）',
  `file_path` VARCHAR(1024) COMMENT '文件在对象存储(MinIO)中的路径',
  `file_hash` VARCHAR(255) COMMENT '文件内容的哈希值，用于去重',
  `admin_user_id` BIGINT COMMENT '上传文件的管理员ID',
  `knowledge_base_id` BIGINT COMMENT '所属知识库ID',
  `upload_id` BIGINT COMMENT '上传id',
  `status` varchar(10) NOT NULL DEFAULT 'uploading' COMMENT '文件处理状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '知识库文件表';

-- ----------------------------
-- 5. 患者上传文件表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `patient_file` (
  `id` BIGINT PRIMARY KEY COMMENT '文件ID，雪花ID',
  `filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
  `file_ext` VARCHAR(50) COMMENT '文件扩展名 (e.g., .pdf, .jpg)',
  `mime_type` VARCHAR(100) COMMENT '文件的MIME类型 (e.g., application/pdf)',
  `size_in_bytes` BIGINT COMMENT '文件大小（字节）',
  `file_path` VARCHAR(1024) COMMENT '文件在对象存储(MinIO)中的路径',
  `file_hash` VARCHAR(255) COMMENT '文件内容的哈希值，用于去重',
  `patient_user_id` BIGINT COMMENT '上传文件的患者ID',
   `upload_id` BIGINT COMMENT '上传id',
  `status` varchar(10) NOT NULL DEFAULT 'uploading' COMMENT '文件处理状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '患者上传文件表';

-- ----------------------------
-- 6. 聊天会话表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `chat_session` (
  `id` BIGINT PRIMARY KEY COMMENT '会话ID，雪花ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `topic` VARCHAR(255) COMMENT '会话主题（可由AI生成）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '聊天会话表';

-- ----------------------------
-- 7. 聊天记录表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `chat_message` (
  `id` BIGINT PRIMARY KEY COMMENT '消息ID，雪花ID',
  `session_id` BIGINT NOT NULL COMMENT '所属会话ID',
  `role` ENUM('user', 'assistant') NOT NULL COMMENT '消息发送者角色',
  `content` TEXT NOT NULL COMMENT '消息内容',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '聊天记录表';

-- ----------------------------
-- 8. 用户记忆表
-- ----------------------------
CREATE TABLE IF NOT EXISTS `memory` (
  `id` BIGINT PRIMARY KEY COMMENT '记忆ID，雪花ID',
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `summary` TEXT NOT NULL COMMENT '关键信息摘要',
  `source_session_id` BIGINT COMMENT '该记忆来源的会话ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否逻辑删除'
) COMMENT '用户记忆表';
