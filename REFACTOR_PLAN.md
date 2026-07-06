# 维修商贸一体化管理系统 — 整改方案

> 适用范围：`source-code/`（含 backend + frontend + 数据库）
> 文档生成：2026-07-06，基于当前 main 分支快照
> 建议节奏：P0 今天关掉，P1 这一周扫完，P2 一个月内捎带做

---

## 总览

| 阶段 | 任务数 | 累计估算 | 完成条件 |
|------|--------|----------|----------|
| **P0 必修** | 3 | ≤2h | dispatch 页 200、JWT 密钥 ≥32 字节、JWT 黑名单 fail-closed |
| **P1 应修** | 6 | 2-3 天 | 8 个蓝图补 RBAC、`additional_claims` 加进 token、`.env.example` 文档一致、补前端 `v-permission`、init_db 不能裸删、补 cross-blueprint 测试 |
| **P2 改进** | 5 | 一月内 | data_scope 显式化、黑名单定时清、`sys_role_permission` 二选一、导出速率限制、`work_order` 字段重构 |

依赖图（箭头 = 后者依赖前者先跑）：

```
P0-1 → P1-2（派单 RBAC）
P0-2 → P1-1（token 升级到含 permissions 字段，需密钥够长）
P0-3 → 长期
P1-1 → P1-2（装饰器可直接读 claims，省一次 DB）
P1-2 → P1-3（前端才知道后端返回什么按钮才显示）
P1-2 → P1-6（测试要等 RBAC 落实才有意义）
```

---

## P0 — 必修（今天）

### ✅ P0-1 修 `dispatch.py:410` 的 500 错误

**目标** 消除派单管理页的 `AttributeError: 'WorkOrder' object has no attribute 'reception_user_id'`。

**位置** `backend/app/blueprints/dispatch.py:410, 411, 422`

**改法**

- 把 3 处的 `o.reception_user_id` 替换为 `o.receiver_id`。
- 顺手把 `d['reception_user_name']` 改成 `d['receiver_name']`（字段名风格和 `work_order` 表一致）。

**验证**

```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/test_blueprints.py -k dispatch -x
```

或浏览器：以任意角色登录 → 进入「派单管理」→ 不再 500，列表正常返回。
查看 `data/logs/flask.log` 不再有该 traceback。

**回滚** `git checkout backend/app/blueprints/dispatch.py`，或 `Edit` 反向替换。

---

### ✅ P0-2 把 JWT 密钥升级到 ≥32 字节

**目标** 消除每次请求的 `InsecureKeyLengthWarning`，避免未来兼容性破窗。

**位置** 根 `.env:8`、`.env.example:6`

**改法**

- 用 `python -c "import secrets; print(secrets.token_urlsafe(64))"` 生成一个 64 字节随机串。
- 写到 `<project-root>/.env` 的 `JWT_SECRET_KEY=` 后。
- `.env.example` 同步留一个明显的占位提示，例如：

```ini
JWT_SECRET_KEY=__SET_ME_TO_RANDOM_64_BYTES__before_first_run__
```

**验证**

```bash
.venv/Scripts/python.exe -c "from app import create_app; create_app('development'); print('ok')"
grep -c "InsecureKeyLengthWarning" data/logs/flask.log
# 应 = 0
```

启动后访问 `/api/health`，确认旧 token 都被踢回 401（密钥改了，所有登录态失效，正常）。

**回滚** 把 `.env` 改回旧值（注意：会让所有已签发的 token 失效一次）。

---

### ✅ P0-3 JWT 黑名单查询改成 fail-closed

**目标** `check_revoked` 出错时**视为已撤销**而不是放行，避免关键时刻认证降级。

**位置** `backend/app/security.py:30-40` 的 `check_revoked` 内部 `except` 块。

**原代码**

```python
except Exception:
    logger.warning('check_revoked DB error (fail-open)', exc_info=True)
    return False  # ← 放行
```

**改法**

- 把 `return False` 改为 `return True`（fail-closed）。
- 同步把注释从 `fail-open` 改为 `fail-closed`。
- 加一行 `logger.error(...)` 升级日志级别（warning → error），触发告警。

**风险** DB 抖动期间所有登录都失效。要权衡：是要「认证高安全」还是「可用性优先」。生产推荐 fail-closed + 监控。

**验证**

```bash
.venv/Scripts/python.exe -m pytest tests/test_jwt_revocation.py -x -v
```

期望所有 `test_jwt_*` 在 DB 异常场景下断言 401。

**回滚** 文件 `Edit` 反向改回 2 行。

---

## P1 — 应修（这一周）

### ✅ P1-1 登录时把 permissions 写进 JWT

**目标** 把登录响应里已查到的 `permissions` / `role_code` 写进 JWT claims，避免每个请求再查一遍 DB；同时让 `permission_helpers.claims_to_perms` 真正能拿到值。

**位置** `backend/app/blueprints/auth.py:53`

**原代码**

```python
access_token = create_access_token(identity=str(user.id))
```

**改法**

```python
from flask_jwt_extended import create_access_token

access_token = create_access_token(
    identity=str(user.id),
    additional_claims={
        'permissions': permissions,
        'role_code': role_code,
    },
)
```

**副作用** 已经签发的旧 token 不带 `permissions`，路由层 `claims_to_perms` 拿空 → 当前所有 `@permission` 装饰器走「用户没有任何权限」分支，会把所有非 admin 请求全 403。**必须配套**：让 `permission_helpers.claims_to_perms` 在 claims 为空时**回退一次查库**（保持向后兼容），或者直接让全员重新登录。

**回退兼容最小补丁**（建议同步改）

`backend/app/services/permission_helpers.py:25-31` 的 `claims_to_perms`：

```python
if claims is None or not isinstance(claims, dict):
    return []
perms = claims.get('permissions') or []
if not perms:
    # 旧 token / 升级期兼容：直接查库
    from flask_jwt_extended import get_jwt_identity
    from models.system import SysUser, SysRole
    uid = get_jwt_identity()
    if uid:
        user = SysUser.query.get(int(uid))
        if user and user.role_id:
            role = SysRole.query.get(user.role_id)
            if role and role.permissions:
                return list(role.permissions)
return perms
```

**验证**

```bash
.venv/Scripts/python.exe -m pytest tests/ -x -v
```

浏览器手动：以 `test1` 登录 → 进「销售管理」应得 403（前端菜单已隐藏，但 curl 测试 API 仍要 403）。

**回滚** `git checkout backend/app/blueprints/auth.py backend/app/services/permission_helpers.py`。

---

### ✅ P1-2 给 8 个蓝图补 `@permission` 装饰器

**目标** 关掉「装饰性 RBAC」漏洞。当前任何登录用户都能改/删客户/商品/资产/供应商/接件状态机/调度/预订/退货单，全部改成带 `@permission` 校验。

**位置** 8 个蓝图文件，待加装饰器路由行号见下表：

| 蓝图 | 文件 | 待加装饰器路由行号 | 建议权限码 |
|------|------|--------------------|------------|
| customer | `customer.py:34,89,103,142,167,181,220,316` | `:view / :add / :edit / :delete` |
| supplier | `supplier.py:33,85,99,136,161,176,212,298` | 同 customer |
| product | `product.py:85,158,200,297,341,360,405,548,574,603,630,654,675,696` | 同上 |
| asset | `asset.py:79,104,180,203,289,348,372,400,505,583,624,703,737` | `asset:view/:add/:edit/:delete` |
| dispatch | `dispatch.py:67,118,145,168,188,215,263,314,328,342,378,439,480` | `dispatch:view/:edit` |
| preorder | `preorder.py:31,65,76,125,164,176` | `preorder:view/:add/:edit/:delete/:convert` |
| return_order | `return_order.py:43,71,82,138,417,513` | `purchase-return:sales-return:view/:add/:edit` |
| receive_actions | `receive_actions.py:54,125,174,236,283,337,400,447,489,527,579,624,673,719,797,860` | `receive:edit`；外送修流程子集单独给 |

**改法样例**（以 `customer.py:104` `create_customer` 为例）

```python
# 原
@bp.route('', methods=['POST'])
@jwt_required()
def create_customer():

# 改
from app.security import permission

@bp.route('', methods=['POST'])
@jwt_required()
@permission('customer:add')
def create_customer():
```

**通用决策表**

```
GET 列表/详情  → 模块:view
POST 创建      → 模块:add
PUT/PATCH 更新 → 模块:edit
DELETE 删除    → 模块:delete
POST 非写业务  → 模块:edit（如状态机转换、审核）
GET 导出/导入  → 模块:view
```

**验证**

```bash
.venv/Scripts/python.exe -m pytest tests/test_cross_blueprint_permission.py -x -v
# 新增：test_asset_permission.py / test_preorder_permission.py / ...（见 P1-6）
```

浏览器：以 `finance_test` 登录 → 试访问 `/api/customers` POST/PUT/DELETE 全 403。

**回滚** 每文件单独 `git checkout`。

---

### ✅ P1-3 前端补 `v-permission` 覆盖更多视图

**目标** 后端补了 RBAC 后，前端菜单/按钮也得跟着藏，否则用户体验割裂。

**位置** `frontend/src/views/*/index.vue`（及其他 .vue）

**盘点现状**（已查）共 5 个文件用了 `v-permission`：

- `customer/index.vue:65`（删除按钮）
- `receive/index.vue:9`（新增按钮）
- `settings/roles.vue:7,54,55,56`
- `settings/users.vue:7,64,65,66,67`
- `workorder/index.vue:22`（新增按钮）

**目标覆盖**（按权限码 → 视图）

| 视图 | 文件 | 应加 v-permission 的按钮 |
|------|------|--------------------------|
| 采购 | `purchase/index.vue` | 列表 新增/编辑/删除/导入/导出 |
| 销售 | `sales/index.vue` | 同上 |
| 商品 | `product/index.vue` | 新增/编辑/删除 |
| 库存 | `inventory/{index,in,out,check}.vue` | 入/出库新增，盘点新增 |
| 仓库 | `warehouse/index.vue` | 新增/编辑 |
| 调拨/调价 | `inventory/{transfer,cost-adjust}.vue` | 新增/编辑 |
| 资产 | `asset/index.vue` | 新增/编辑/删除/报废 |
| 客户/供应商 | `customer/supplier/index.vue` | 新增/编辑（删除已有） |
| 财务子页 | `finance/*.vue` | 应收/应付/收/付/工资/费用/对账的编辑 |
| 派单 | `dispatch/index.vue` | 派单/改派（技师只读） |

**改法样例**

```vue
<!-- 前 -->
<el-button type="primary" :icon="Plus" @click="handleAdd">新增客户</el-button>
<!-- 后 -->
<el-button type="primary" :icon="Plus" v-permission="'customer:add'" @click="handleAdd">新增客户</el-button>
```

**注意**

- `frontend/src/directives/permission.js` 已经在 `mounted` / `updated` 时检查，全局注册在 `main.js`，无需改 directive。
- `v-permission` 数组重载不会触发 `updated`，**动态列表行内的按钮**如需权限切换，建议用 `v-show` + `hasPermission()` 显式控制，或在 store 变化时 refresh 组件。

**验证**

- 浏览器以 `test1`（技师）登录 → 应看不到「采购管理」侧边栏 → 直接访问 `/purchase` 应 403 或重定向。
- 以 `finance_test` 登录 → 进入「客户管理」看不到新增按钮。

**回滚** 文件级 `git checkout`，或在前端删除 `v-permission` 属性。

---

### ✅ P1-4 清理 `backend/.env.example` 的 MySQL/Redis 字样

**目标** 文档与代码一致；避免新人按 `.env.example` 配 MySQL 卡住。

**位置** `backend/.env.example:9-12, 18, 26-28`

**改法**（最小替换）

```ini
# 原
DATABASE_URL=mysql+pymysql://repair_user:Repair@2024@mysql:3306/repair_system?charset=utf8mb4
# ↓ 替换为
# 数据库：留空走 SQLite 默认 data/repair_system.db；自定义用绝对路径
# DATABASE_URL=sqlite:///D:/myapp/data/repair.db
DATABASE_URL=

# 原
REDIS_URL=redis://redis:6379/0
# ↓ 替换为
# Redis 已移除（JWT 黑名单改用 SQLite jwt_blacklist 表）
# REDIS_URL=（已废弃，保留仅为兼容历史 import）

# 原
UPLOAD_FOLDER=/app/uploads
# ↓ 替换为
UPLOAD_FOLDER=data/uploads

# 原
SESSION_COOKIE_SECURE=true
# ↓ 替换为
SESSION_COOKIE_SECURE=false  # 生产 HTTPS 改为 true

# 原
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=
# ↓ 替换为
DEFAULT_ADMIN_PASSWORD=123456
```

**附带** README.md 第 26-28 行 setup 默认账号的解释要不要改也同步扫一遍。

**验证**

```bash
cat backend/.env.example | grep -E "mysql|redis"
# 应 0 行
```

**回滚** `git checkout backend/.env.example`。

---

### ✅ P1-5 `init_db.py` 加 `--force` 开关，默认拒绝覆盖

**目标** 防止新人不小心 `python init_db.py` 把整个业务库删了。

**位置** `backend/scripts/init_db.py:42, 277-291`

**改法**

1. 在 `init_database()` 开头加：

```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--force', action='store_true',
                    help='已存在数据库时也覆盖（危险：会清空所有业务数据）')
args, _ = parser.parse_known_args()
```

2. `db_file.unlink()` 前：

```python
if db_file.exists() and not args.force:
    raise RuntimeError(
        f'数据库已存在：{db_file}\n'
        f'如确认要重建，请加 --force 参数（会清空全部业务数据）。'
    )
```

3. `if __name__ == '__main__': init_database()` 不变。

**验证**

```bash
cd backend
.venv/Scripts/python.exe scripts/init_db.py
# 应抛 RuntimeError "数据库已存在…"
.venv/Scripts/python.exe scripts/init_db.py --force
# 应正常重建
```

**回滚** `git checkout backend/scripts/init_db.py`。

---

### ✅ P1-6 加 cross-blueprint 集成测试

**目标** 给 P1-2 补的 8 个蓝图写「技师无权限」测试，避免下次改 backout 又漂移。

**位置** `backend/tests/test_cross_blueprint_permission.py` 是模板，每新建一个 `test_<module>_permission.py` 仿造它：

```python
# test_<module>_permission.py
import pytest

TECH_PERMS = [...]  # 从 init_db.py 复制


@pytest.fixture
def app(): ...  # 同 test_cross_blueprint_permission.py


def _make_user(db, username, perms, role_code='technician'): ...

# 加 6 个 case：技师 CRUD + admin CRUD 通过 + 财务/库管按文档拿他们应有的权限
def test_tech_cannot_create_customer(app, db): ...
def test_tech_cannot_update_customer(app, db): ...
def test_tech_cannot_delete_customer(app, db): ...
def test_admin_can_create_customer(app, db): ...
# ...
```

**覆盖清单**（新增以下测试文件）

- `tests/test_customer_permission.py`
- `tests/test_supplier_permission.py`
- `tests/test_product_permission.py`
- `tests/test_asset_permission.py`
- `tests/test_preorder_permission.py`
- `tests/test_dispatch_permission.py`
- `tests/test_return_order_permission.py`
- `tests/test_receive_actions_permission.py`

**验证** `pytest tests/ -k permission -v` 全绿。

**回滚** `rm backend/tests/test_*_permission.py`。

---

## P2 — 改进（一月内）

### P2-1 把 `data_scope` 显式化进 `sys_role`

**背景** 当前 `permission_helpers.DATA_SCOPED_ROLES = {'technician'}` 是硬编码角色名，未来如果改角色名（如「维修技师」 → 「工程师」），数据隔离就破。

**位置** `backend/models/system/user.py:30-40`、`backend/scripts/init_db.py:213-267`、`backend/app/services/permission_helpers.py:21`

**改法**

1. `sys_role` 加一列 `data_scope INTEGER DEFAULT 0`（0 = 全量，1 = 按 `assigned_user_id` 隔离）。
2. `init_db.py` 的 `ROLES` 元组扩展为五元组：`(name, code, perms, desc, data_scope)`。
3. `permission_helpers.is_data_scoped(role)` 改为查 `role.data_scope == 1`。

**验证** 用 `test1` 登录 → 进工单列表 → 应只看自己接的；以 `admin` 登录 → 看全部。

**回滚** 删列 + `git checkout` 三个文件。

---

### P2-2 JWT 黑名单改成 APScheduler 定时清理

**背景** 当前 `cleanup_expired_blacklist` 只在 Flask 启动跑一次（`app/__init__.py:62`），长期运行的实例黑名单表无限增长。

**位置** `backend/app/__init__.py:60-64`

**改法**

```python
from apscheduler.schedulers.background import BackgroundScheduler

sched = BackgroundScheduler()
sched.add_job(cleanup_expired_blacklist, 'cron', hour=3)  # 每天凌晨 3 点
sched.start()
```

并在 `backend/requirements.txt` 加 `APScheduler==3.10.4`。

**注意** 测试环境 `TestingConfig` 要把 sched 关掉，避免 fixture 冲突。

**验证** 启动日志可见 `Started background scheduler`；插一条 `expires_at` 过期记录，等次日观察 `DELETE` 日志。

**回滚** 删两行 + `pip uninstall APScheduler`。

---

### P2-3 `sys_role_permission` 表的处置（二选一）

**背景** 这张表在 `init_db.py:79-84` 建了，但 `_seed` 根本没写入，代码也没读它。

**位置** `backend/database/init.sql:79-84`、`backend/scripts/init_db.py`

**方案 A（推荐）** 删表、删代码。它没用且在 schema 里占位。

**方案 B** 改造为「角色-perm 多对多」，把 `sys_role.permissions JSON` 字段迁出到这张表。复杂、收益小、不建议。

**验证** 方案 A 走完 `init_db.py` + `pytest tests/` + 浏览器登录测试技师 → 权限不变。

---

### P2-4 导出接口加速率限制 / 单次条数限制

**背景** `PER_PAGE_MAX = 200`，导出类接口（多个 `*/export`）不限速，可能让数据库锁死。

**位置** `backend/app/config.py:89-90`、各 `export_to_excel` 调用点

**改法**

1. 新增 `PER_PAGE_EXPORT_LIMIT = 1000`，导出接口最大返回 1000 行。
2. `flask-limiter==3.5.0` 加入 `requirements.txt`，给 `/api/<mod>/export` 加 `@limiter.limit("10/minute")`。

**验证** 连续点 11 次导出 → 第 11 次 429。

**回滚** `pip uninstall flask-limiter` + 删装饰器。

---

### P2-5 `work_order` 表拆解

**背景** `work_order` 单表 ~140 字段（数据库初始化 SQL 行 997-1141），型号/网络/施工/验收/网络拓扑等字段混在一张表。

**位置** `backend/database/init.sql:997-1141`、`backend/models/workorder/*.py`（按子目录已拆）

**改法**（**慎做**，改前必须先备份 db）

- 把「工单扩展字段」（监控/网络/施工/弱电/打印机/摄像机…）拆到 `work_order_extend` 或 `wo_dynamic_field`（表已存在，已经设计好动态字段，只是实际数据没迁过去）。
- 工单主表保留业务核心字段（客户/费用/状态/分配等）。

**风险** 改这表影响所有工单相关蓝图，**强烈建议放在 P2 末尾**，且在生产前必须有完整备份 + 回滚脚本。

**验证** `pytest -x -v` + 浏览器手动跑一遍工单新增 → 完成全流程。

**回滚** `git checkout` + 从备份恢复 db 文件。

---

## 收尾验证清单（修完后跑一遍）

```bash
# 1. 后端单测
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/ -v

# 2. 数据完整性
.venv/Scripts/python.exe -c "import sqlite3; conn=sqlite3.connect('../data/repair_system.db'); print('TABLES:', len(conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"').fetchall())); print('USERS:', conn.execute('SELECT count(*) FROM sys_user').fetchone()[0])"

# 3. 健康检查
curl http://localhost:5000/api/health
# 期望 {"status":"healthy","db":true}

# 4. 前端编译
cd ../frontend
npm run build  # 必须 0 warning + dist/ 重新生成

# 5. 浏览器手测账号矩阵
# admin            → 全菜单 + 全按钮
# test1            → 只看工单/接件/资产/库存查询/客户查看
# finance_test     → 财务全套 + 业务单据查看（无商品/system）
# warehouse_test   → 库存全套 + 商品采购 + 接件/工单查看
```

---

## 更新记录

| 日期 | 修改人 | 内容 |
|------|--------|------|
| 2026-07-06 | Claude Code 审计 | 初稿，基于审查问题清单整理 |
