# Task E-1: backend/.env.example 清理

## 目标
把 backend 路径下的 `.env.example`（MySQL/Redis 时代遗留）改成 SQLite 时代的示例。

## 涉及文件
`source-code/backend/.env.example`

## 改法
完整替换文件内容为：

```ini
# Repair System - 后端开发配置（拷贝为 .env 后可修改）
# ============================================================

# Flask 运行环境：development / production / testing
FLASK_ENV=development

# JWT 密钥（生产环境必须修改为长随机字符串）
JWT_SECRET_KEY=RepairSystemSecretKey2024

# SQLite 数据库路径留空 → config.py 自动用项目根 data/repair_system.db（绝对路径）
# 如需自定义，写绝对路径：DATABASE_URL=sqlite:///D:/myapp/data/repair.db
DATABASE_URL=

# 上传文件目录
UPLOAD_FOLDER=data/uploads

# 上传文件大小上限（MB）
MAX_CONTENT_LENGTH_MB=16

# CORS 允许的来源（逗号分隔；开发用 localhost:5173）
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Cookie 安全（生产 HTTPS 设为 true）
SESSION_COOKIE_SECURE=false

# Talisman 安全头（生产设为 true）
TALISMAN_ENABLED=false

# Setup 端点开关（首次部署后可设为 false）
SETUP_ENABLED=true

# 默认管理员密码（init_db 时使用）
DEFAULT_ADMIN_PASSWORD=123456
```

## 不要碰
- 不要碰根 `.env`（那是 A-1 已经处理过的）
- 不要碰 `backend/extensions.py`、`backend/app/config.py`

## 验证
```bash
cat source-code/backend/.env.example | grep -E "mysql|redis"
# 应 = 0 行
diff source-code/backend/.env.example source-code/.env.example
# 应该很像，可能小差异（Cookie 默认值不同）
```

## 提交
```
docs(env): backend/.env.example 与 SQLite 现状对齐

- 删除 mysql+pymysql 与 redis URL 示例
- 改为 DATABASE_URL 留空走 SQLite 默认路径
- DEFAULT_ADMIN_PASSWORD 替代老的 INITIAL_ADMIN_PASSWORD
```

## 回滚
```bash
git checkout source-code/backend/.env.example
```
