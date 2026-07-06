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
5. 默认账号见 [默认账号与角色权限](#默认账号与角色权限) 一节

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

## 默认账号与角色权限

首次启动（`data/repair_system.db` 不存在）会自动建库并写入 4 个角色 + 2 个用户；其余 2 个测试用户见 [重置数据库](#重置数据库)。

| 账号 | 密码 | 角色 | 用途 |
|------|------|------|------|
| `admin` | 123456 | 系统管理员 | 全权限（`*` 通配符自动展开为 112 项） |
| `test1` | 123456 | 维修技师 | 见下方"角色权限矩阵" |
| `finance_test` | 123456 | 财务 | 见下方 |
| `warehouse_test` | 123456 | 库管 | 见下方 |

### 角色权限矩阵

权限码命名统一 `模块:操作`（如 `workorder:view`、`workorder:add`），与前端 `frontend/src/layouts/MainLayout.vue` 的 `menuPermissionMap` 一一对应。`:view` 控制**菜单可见性**，`:add`/`:edit`/`:delete` 控制**按钮可见性**。

| 模块 | admin | technician | finance | warehouse |
|------|:-----:|:----------:|:-------:|:---------:|
| 首页 dashboard | ✓ | ✓ | ✓ | ✓ |
| 工单 workorder | ● | 增改 | 查看 | 查看 |
| 接件 receive | ● | 增改 | — | 查看 |
| 派单 dispatch | ● | 查看 | — | — |
| 报价 quote | ● | — | — | — |
| 资产 asset | ● | 查看 | — | — |
| 客户 customer | ● | 查看 | 查看 | — |
| 供应商 supplier | ● | — | 查看 | 查看 |
| 商品 product | ● | — | — | 增改 |
| 销售 sales | ● | — | 查看 | — |
| 采购 purchase | ● | — | 查看 | 增改 |
| 采购预订 / 销售预订 | ● | — | — | — |
| 采购退货 / 销售退货 | ● | — | — | — |
| 库存查询 inventory | ● | 查看 | 查看 | 查看 |
| 入库 inventory-in | ● | — | — | 增改 |
| 出库 inventory-out | ● | — | — | 增改 |
| 库存盘点 inventory-check | ● | — | — | 增改 |
| 仓库 warehouse | ● | 查看 | — | 增改 |
| 库存变动明细 inventory-log | ● | 查看 | — | 查看 |
| 调拨 transfer | ● | — | — | 增改 |
| 成本调价 cost-adjust | ● | — | — | 增改 |
| 财务 finance（含应收/应付/收付/工资/费用/对账/统计） | ● | — | 增改（**无删除**） | — |
| 发票 invoice | ● | — | ✓（随 finance:view） | — |
| 用户管理 settings-users | ● | — | — | — |
| 角色管理 settings-roles | ● | — | — | — |
| 商品分类/单位/打印模版 settings | ● | — | — | — |
| 操作日志 settings-log | ● | — | — | — |

说明：
- `●` = 全部动作（增删改查导通通有，等价于 `["*"]`）
- `增改` = 拥有 `:add` + `:edit`，无 `:delete`
- `查看` = 仅 `:view`，可看菜单/列表但所有动作按钮隐藏
- `—` = 不可见

权限基线可在「系统设置 → 角色管理」页面上调整（后端 `api/auth/login` 返回的 `permissions` 字段就来自 `sys_role.permissions` JSON）。

### 重置数据库

```bash
# 停止服务
stop.bat   # 或 ./stop.sh

# 删 db 文件再跑 init 脚本（会自动重建 schema + 重新 seed）
cd source-code
rm -f data/repair_system.db data/repair_system.db-wal data/repair_system.db-shm
backend/.venv/Scripts/python.exe backend/scripts/init_db.py
# 或重新 init_db.py；会自动建库
```

> 注意：删库会同时清除 `sys_user` / `sys_role` / `sys_permission` / 所有业务表。  
> 重新 init 后只有 admin 和 test1 两个用户。`finance_test` / `warehouse_test` 请通过 admin 登录后在「系统设置 → 用户管理」页面手动创建（角色绑定到对应角色码）。

### 鉴权实现说明

- 后端走 Flask-JWT-Extended；登录同时返回 `Set-Cookie: access_token_cookie` 和 JSON 里的 `token` 字段
- 后端 `JWT_TOKEN_LOCATION = ['headers', 'cookies']`（`backend/app/config.py:27`）：Authorization header 优先（前端 `stores/user.js` 把 token 存 localStorage 后用 `Bearer` 头传），cookie 作为自动登录兜底。Header 模式不要求 CSRF token
- 前端登录响应字段是 `data.userInfo`（不是 `user`），由 `stores/user.js` 解析；store 同步把 `permissions` 写入，以便 `MainLayout.vue` 渲染侧边栏时按 `menuPermissionMap` 过滤

---

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

## 许可证

本项目仅供学习和内部使用。