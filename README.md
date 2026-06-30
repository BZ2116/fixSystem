# 维修商贸一体化管理系统（便携版）

## 系统概述

维修商贸一体化管理系统的便携部署版本。**无需 Docker、无需 MySQL、无需 Redis**，解压即用，数据存本地 SQLite 文件。

适用于：
- 单店 / 小团队（≤ 5 并发用户）
- 跨电脑迁移（zip → 解压 → 启动）
- 离线 / 内网环境

## 技术栈

### 前端
- Vue 3.2.47 + Vite 4.4.9 + Element Plus 2.2.28

### 后端
- Python 3.11 + Flask 2.3.3 + Flask-SQLAlchemy 3.0.5 + Flask-JWT-Extended 4.5.2

### 数据
- SQLite（Python 内置，单文件）
- 本地文件系统（上传文件）

## 快速开始

### Windows

1. 安装 Python 3.11+：<https://www.python.org/downloads/>
2. 解压项目到任意目录
3. 双击 `start.bat`
4. 浏览器打开 <http://localhost:5173>
5. 默认账号：`admin` / `123456`

### Linux / macOS

```bash
chmod +x start.sh stop.sh
./start.sh
```

首次启动会自动：
- 复制 `.env.example` → `.env`
- 创建 `backend/.venv/` 并安装依赖
- 执行 `backend/scripts/init_db.py` 建库 + 种子数据
- 安装 `frontend/node_modules/`
- 启动 Flask（5000）+ Vite（5173）

## 目录结构

```
repair-system/
├── backend/                    # 后端代码
│   ├── app/                    # 工厂 + blueprints + services + utils
│   ├── models/                 # SQLAlchemy 模型
│   ├── database/init.sql       # SQLite schema
│   ├── scripts/                # init_db / start_dev
│   ├── tests/
│   └── requirements.txt
├── frontend/                   # 前端代码（dist/ 预构建在 zip 中）
├── data/                       # ★ 运行时数据（备份这个目录就够了）
│   ├── repair_system.db        # SQLite 主库
│   ├── uploads/                # 上传文件
│   ├── logs/                   # flask.log / vite.log
│   └── .pids/                  # flask.pid / vite.pid
├── docs/
│   ├── superpowers/specs/
│   ├── superpowers/plans/
│   └── archive/                # 旧 MySQL schema + docker 文件（参考用）
├── start.bat / start.sh        # 开发模式入口
├── start_prod.bat / start_prod.sh  # 生产模式入口
├── stop.bat / stop.sh          # 停止服务
├── .env.example
├── .gitignore
├── README.md
└── VERSION.txt
```

## 数据备份

```bash
# 1. 停止服务
stop.bat   # 或 ./stop.sh

# 2. 备份整个 data/ 目录
xcopy /E data\ data_backup_20260630\
# 或 Linux：cp -r data/ data_backup_20260630/

# 3. 重启
start.bat
```

仅备份 `data/repair_system.db*` 三个文件即可完整恢复业务数据。

## 跨电脑迁移

在源机器上：
```cmd
build_portable.bat 2026.06.30
```
产出 `repair-system-portable-v2026.06.30.zip`（含预构建的 `frontend/dist/`）。

在目标机器上：
1. 安装 Python 3.11+
2. 解压 zip
3. **如果需要带上旧数据**：把旧机器的 `data/repair_system.db*` 覆盖到解压目录的 `data/`
4. 双击 `start.bat` → 自动检测 `data/repair_system.db` 已存在，跳过初始化

## 生产模式

- Windows：`start_prod.bat`（用 waitress / flask run）
- Linux：`./start_prod.sh`（用 gunicorn -w 2）
- 前端使用 `frontend/dist/` 预构建静态文件（不是 dev server）

## 限制

- SQLite 串行化写：≤ 5 并发用户适用
- 没有全文搜索（`LIKE '%xxx%'` 仍可用）
- 没有对象存储（上传文件走本地 `data/uploads/`）

## 故障排查

| 问题 | 解决 |
|------|------|
| `python: command not found` | 安装 Python 3.11+ 并加入 PATH |
| `OperationalError: database is locked` | 关闭其他连接，或删除 `data/.pids/*.pid` 后重启 |
| 前端 404 | 检查 `frontend/dist/` 是否存在；缺失则 `cd frontend && npm run build` |
| 端口 5000/5173 占用 | 改 `start_dev.py` 中的端口，或 `netstat` / `lsof` 找到占用进程 |

## 技术支持

查看日志：
- `data/logs/flask.log`
- `data/logs/vite.log`

## 归档清理（2026-07-14 后执行）

两个过渡性目录将在 2 周后删除：
- `docs/archive/docker-configs/` —— 旧 docker 文件
- `docs/archive/database_complete_v3.sql` —— MySQL 原版 schema（参考用）

届时会再发一个 commit 完成清理。

## 许可证

本项目仅供学习和内部使用。