# Portable Zip Verify & Wrap-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 验证现有 portable zip 在干净机器上解压即用，并清理仓库状态到「可分发」级别。

**Architecture:** 分四阶段线性推进：仓库清理 → 重打 zip → 端到端验证 → archive + 文档收尾。每阶段独立 commit，验证失败可回滚上一阶段。

**Tech Stack:** Python 3.11+ / Flask / SQLite / Vue 3 (无新增技术栈，沿用 2026-06-30 迁移后的栈)

**Reference Spec:** `docs/superpowers/specs/2026-07-03-portable-zip-verify-and-wrapup-design.md`

---

## 文件结构

**本计划涉及的文件**：

| 类型 | 路径 |
|------|------|
| 修改 | `backend/app/config.py`, `backend/app/security.py`, `backend/app/blueprints/auth.py` |
| 修改 | `backend/models/_base.py` |
| 修改 | 各 model 文件（asset/account/stock/flow/warehouse/template/info/order/return_order/device/order/order/receipt/quote/record/base/base/user/office/types/order） |
| 新增（git 跟踪） | `backend/tests/test_jwt_revocation.py` |
| 修改 | `.gitignore` |
| 修改 | `README.md` |
| 修改 | `VERSION.txt` |
| 产出（不入库） | `repair-system-portable-v2026.07.03.zip` |
| 删除（工作树） | `verify_bigint.db`, `backend/instance/dev.db`, `backend/instance/instance_smoke.db` |
| 删除（git 跟踪） | `docs/archive/docker-configs/`, `docs/archive/database_complete_v3.sql` |
| 摘出跟踪 | 30+ `__pycache__/` 下的 `.pyc` 文件 |

**每个任务的隔离粒度**：每任务一个 commit，commit 之间互不依赖，回滚安全。

---

## Phase 1: 仓库状态审计与清理

### Task 1: 审计并提交 config.py / security.py / auth.py 改动

**Files:**
- Modify (verify, then commit): `backend/app/config.py`
- Modify (verify, then commit): `backend/app/security.py`
- Modify (verify, then commit): `backend/app/blueprints/auth.py`

- [ ] **Step 1: 审查 config.py 改动**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git diff backend/app/config.py
```

预期看到：移除 MySQL 专属配置，加 `busy_timeout=5`、`check_same_thread=False`，`SQLALCHEMY_DATABASE_URI` 默认指向 `data/repair_system.db`。**不应**出现 `mysql`、`pymysql`、`utf8mb4` 字样。

- [ ] **Step 2: 审查 security.py 改动**

```bash
git diff backend/app/security.py
```

预期看到：`check_revoked` 改为查 SQLite `jwt_blacklist` 表；`revoke_token` 改为 INSERT 到 SQLite；新增 `cleanup_expired_blacklist()`。**不应**再有 `redis_client`、`REVOKED_JTI_KEY` 实际调用。

- [ ] **Step 3: 审查 auth.py 改动（C2 cookie 修复）**

```bash
git diff backend/app/blueprints/auth.py
```

预期看到：登录响应里 `set_access_cookies(response, access_token)`、`set_refresh_cookies(...)`；登出时 `unset_access_cookies`、`unset_refresh_cookies`，并调用 `revoke_token`。

- [ ] **Step 4: 若三文件改动符合预期，一次性 commit**

```bash
git add backend/app/config.py backend/app/security.py backend/app/blueprints/auth.py
git commit -m "$(cat <<'EOF'
refactor(backend): commit pending SQLite migration changes for config/security/auth

config: 默认 URI 指向 data/repair_system.db，加 SQLite busy_timeout
security: JWT 黑名单从 Redis 迁移到 SQLite jwt_blacklist 表
auth: 登录/登出同步 set/unset cookies (C2 fix)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: 若任一文件不符合预期（出现 MySQL/redis 残留或新功能）**

**停止本任务**，把不符合预期的文件 `git checkout -- <file>` 还原，记录到任务备注，**不**混进本次 commit。

---

### Task 2: 审计并提交 models/_base.py（TimestampMixin）

**Files:**
- Modify (verify, then commit): `backend/models/_base.py`

- [ ] **Step 1: 审查 _base.py 改动**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git diff backend/models/_base.py
```

预期看到：`TimestampMixin` 类，包含 `created_at` / `updated_at` 两个 `db.Column(db.DateTime)`，`updated_at` 带 `onupdate=datetime.now`。

- [ ] **Step 2: 符合预期 → commit**

```bash
git add backend/models/_base.py
git commit -m "$(cat <<'EOF'
feat(models): add TimestampMixin (replaces MySQL ON UPDATE CURRENT_TIMESTAMP)

SQLAlchemy 的 onupdate 钩子在 app 层运行，SQLite 兼容。

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: 审计并批量提交 model 文件 SQLite 兼容改动

**Files:**
- Modify (verify, then commit): 20+ 个 model 文件（`backend/models/*/.*.py` 中除 `_base.py` 外的所有 uncommitted 文件）

- [ ] **Step 1: 列出所有 uncommitted model 文件**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git diff --name-only | grep "backend/models/.*\.py$"
```

预期看到类似：
```
backend/models/asset/asset.py
backend/models/customer/base.py
backend/models/dispatch/record.py
backend/models/finance/account.py
backend/models/inventory/flow.py
backend/models/inventory/stock.py
backend/models/inventory/warehouse.py
backend/models/printer/template.py
backend/models/product/info.py
backend/models/purchase/order.py
backend/models/purchase/return_order.py
backend/models/quote/order.py
backend/models/receive/device.py
backend/models/receive/order.py
backend/models/sales/invoice.py
backend/models/sales/order.py
backend/models/sales/receipt.py
backend/models/supplier/base.py
backend/models/system/office.py
backend/models/system/user.py
backend/models/workorder/order.py
backend/models/workorder/types.py
```

- [ ] **Step 2: 抽样审查 3 个改动最大的 model**

```bash
git diff backend/models/finance/account.py | head -80
git diff backend/models/inventory/flow.py | head -80
git diff backend/models/workorder/order.py | head -80
```

预期看到典型 SQLite 兼容改动：
- `db.BigInteger` 主键（兼容 SQLite 自增）
- `db.Numeric(precision, scale)` 替代 `DECIMAL`
- `db.JSON` 替代 MySQL JSON 列
- 去掉 `mysql__` engine options
- 引用 `from models._base import TimestampMixin`

**禁止出现**：新功能、未在 spec 范围内的行为变更。

- [ ] **Step 3: 检查是否有"无意义"或可疑改动**

```bash
git diff --stat | grep "backend/models/"
```

若任一文件改动 > 50 行，单独 review 确认没有夹带新功能。**禁止在本次 commit 加新功能**。

- [ ] **Step 4: 一次性 commit 所有 model 改动**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git add backend/models/
git commit -m "$(cat <<'EOF'
refactor(models): SQLite-compatible column types across all models

- db.Numeric(precision, scale) 替代 MySQL DECIMAL
- db.JSON 替代 MySQL JSON 列
- BigInteger PK 依赖 SQLite INTEGER 自增
- 部分 model 引入 TimestampMixin

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: 摘出 `__pycache__` 跟踪

**Files:**
- Modify (git index only): 所有 `**/__pycache__/*.pyc` 文件（保留本地文件，仅从 git 索引摘出）

- [ ] **Step 1: 列出被跟踪的 __pycache__ 文件**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git ls-files | grep "__pycache__" | head -10
```

预期：30+ 个 `.pyc` 文件。

- [ ] **Step 2: 从 git 索引摘出（保留本地）**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git ls-files -z | grep -z "__pycache__" | xargs -0 -I {} git rm --cached "{}"
```

或更直接：
```bash
git rm --cached -r backend/__pycache__ backend/app/__pycache__ backend/models/__pycache__ backend/tests/__pycache__
```

如果上面报错说某些子目录不存在，根据 `git ls-files` 实际输出调整路径。

- [ ] **Step 3: 验证本地文件还在但 git 不再跟踪**

```bash
ls backend/app/__pycache__/config.cpython-313.pyc  # 文件存在
git ls-files backend/app/__pycache__/config.cpython-313.pyc  # 无输出
```

- [ ] **Step 4: commit**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git commit -m "$(cat <<'EOF'
chore(git): untrack __pycache__ directories

历史已添加 .gitignore 但 pyc 文件先于 ignore 被 git add 进来。
本次仅从索引摘出，本地文件保留。

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: 提交 test_jwt_revocation.py + 验证测试通过

**Files:**
- Add (git track): `backend/tests/test_jwt_revocation.py`

- [ ] **Step 1: 阅读测试文件内容**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
cat backend/tests/test_jwt_revocation.py
```

预期：5 个测试函数（`test_login_sets_access_cookie` / `test_cookie_works_for_protected_endpoint` / `test_no_cookie_still_401` / `test_logout_revokes_token` / `test_revoke_token_writes_revoked_at` / `test_orm_insert_sys_user_writes_id`），每个测试都有 docstring 说明意图（C1 撤销 / C2 cookie 下发）。

- [ ] **Step 2: 检查文件是否已在 conftest.py 等地方引用**

```bash
grep -rn "test_jwt_revocation" backend/tests/ --include="*.py" | grep -v __pycache__
```

预期：无输出（这是一个独立测试文件，不被 import）。

- [ ] **Step 3: 跑测试套件，验证 jwt_revocation 测试通过**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code/backend"
python -m pytest tests/test_jwt_revocation.py -v
```

预期：6 个测试全 PASS。
- 若失败 `ModuleNotFoundError`：先 `pip install -r requirements.txt pytest`
- 若失败 `ImportError`：检查 import 路径是否对得上当前 app layout
- 若失败 `OperationalError: no such table`：本次 spec 的「失败处理」路径——回到 Task 7 之后补 init.sql

- [ ] **Step 4: commit**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git add backend/tests/test_jwt_revocation.py
git commit -m "$(cat <<'EOF'
test(jwt): add C1/C2 regression for revocation and cookie auth

C1: logout 后旧 token/cookie 访问受保护端点必须 401
C2: 登录必须 set_access_cookies，cookie-only 模式后续请求不能 401
另含 BigInteger PK 在 SQLite 自增的回归测试。

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: 清理测试残留 + 补 `.gitignore`

**Files:**
- Delete (working tree): `verify_bigint.db`, `backend/instance/dev.db`, `backend/instance/instance_smoke.db`
- Modify: `.gitignore`（追加 `backend/instance/`）

- [ ] **Step 1: 确认要删除的文件确实存在**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
ls verify_bigint.db
ls backend/instance/ 2>/dev/null
```

预期：`verify_bigint.db` 存在；`backend/instance/` 目录下有 `dev.db` 和 `instance_smoke.db`。

- [ ] **Step 2: 删除测试残留（不进 git，本地直接删）**

```bash
rm -f verify_bigint.db
rm -f backend/instance/dev.db backend/instance/instance_smoke.db
```

Windows PowerShell 等价：
```powershell
Remove-Item verify_bigint.db -ErrorAction SilentlyContinue
Remove-Item backend/instance/dev.db, backend/instance/instance_smoke.db -ErrorAction SilentlyContinue
```

- [ ] **Step 3: 在 `.gitignore` 末尾追加 `backend/instance/`**

打开 `C:/Users/BruceZhao/Desktop/source-code/source-code/.gitignore`，**在最后一行后追加**：

```
# 测试运行时 SQLite 实例（conftest / smoke 产生）
backend/instance/
```

- [ ] **Step 4: commit**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git add .gitignore
git commit -m "$(cat <<'EOF'
chore(gitignore): exclude backend/instance/ test artifacts

test_smoke / conftest 在 backend/instance/ 写临时 db，
不应入库。删除 verify_bigint.db 等残留。

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: 跑完整 pytest 套件

- [ ] **Step 1: 跑全部测试**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code/backend"
python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_phase1.txt
```

预期：所有测试 PASS（test_smoke / test_utils / test_blueprints / test_jwt_revocation）。

- [ ] **Step 2: 若有失败，按错误类型处理**

| 错误 | 处理 |
|------|------|
| `no such table: xxx` | 补 `backend/database/init.sql`，回到 Phase 1 新增 Task commit |
| `BigInteger PK not populated` | 修对应 model（已在 test_jwt_revocation 覆盖） |
| `ModuleNotFoundError` | `pip install -r requirements.txt pytest` |
| `fixture not found` | 检查 conftest.py 兼容性 |
| 其他 | 记入任务备注，单独立 fix commit，**不**绕过 |

- [ ] **Step 3: 若无失败（无需 commit）**

记录到本任务备注：「Phase 1 pytest 全 PASS」。

---

## Phase 2: 重打 zip

### Task 8: 重打 portable zip

**Files:**
- 产出（不入库）：`repair-system-portable-v2026.07.03.zip`

- [ ] **Step 1: 删除旧 zip**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
rm -f repair-system-portable-*.zip
```

- [ ] **Step 2: 跑 build_portable.py**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
python build_portable.py
```

预期输出（节选）：
```
[build] writing repair-system-portable-v2026.07.03.zip
  + dir : backend (X files)
  + dir : frontend (Y files)
  + dir : data (Z files)
  + dir : docs (W files)
  + file: start.bat
  + file: start.sh
  ...
[build] done: repair-system-portable-v2026.07.03.zip (N.N MB)
```

- [ ] **Step 3: 验证 zip 生成**

```bash
ls -la repair-system-portable-v2026.07.03.zip
```

预期：文件存在，大小 < 10MB（应约 2-3MB）。

- [ ] **Step 4: 抽样验证 zip 内容**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
python -c "
import zipfile
z = zipfile.ZipFile('repair-system-portable-v2026.07.03.zip')
names = z.namelist()
print('Total files:', len(names))
# 必须包含
must = ['start.bat', 'start.sh', 'README.md', 'VERSION.txt',
        'backend/requirements.txt', 'backend/database/init.sql',
        'backend/scripts/init_db.py', 'backend/scripts/start_dev.py',
        'frontend/dist/index.html']
missing = [m for m in must if m not in names]
print('Missing:', missing if missing else 'NONE')
# 必须不包含
forbidden = [n for n in names if '__pycache__' in n or 'node_modules' in n or '.pyc' in n]
print('Forbidden in zip:', forbidden[:5] if forbidden else 'NONE')
"
```

预期：`Missing: NONE`，`Forbidden in zip: NONE`。

- [ ] **Step 5: 若 build 失败或 zip 缺/多文件**

修复 `build_portable.py`（或 `.bat`）的 INCLUDE/EXCLUDE 规则，commit 后重跑本任务。

---

## Phase 3: 端到端验证

> 本阶段在干净目录模拟「目标机器」。所有步骤在临时目录进行，**不**污染主项目目录。

### Task 9: 准备干净验证目录

- [ ] **Step 1: 创建临时目录**

```bash
# Windows (PowerShell 或 cmd)
VERIFY_DIR="D:/portable-verify"
mkdir -p "$VERIFY_DIR"
```

若 `D:/` 无写权限，用 `%TEMP%/portable-verify` 或用户目录下的临时目录。

- [ ] **Step 2: 复制 zip 到临时目录并解压**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
cp repair-system-portable-v2026.07.03.zip "D:/portable-verify/"
cd "D:/portable-verify"
# Windows PowerShell 解压
Expand-Archive -Path repair-system-portable-v2026.07.03.zip -DestinationPath . -Force
```

预期：`D:/portable-verify/` 下出现 `start.bat`, `start.sh`, `backend/`, `frontend/`, `data/`, `README.md` 等。

- [ ] **Step 3: 验证解压完整**

```bash
ls "D:/portable-verify/start.bat" "D:/portable-verify/backend/requirements.txt" "D:/portable-verify/frontend/dist/index.html" "D:/portable-verify/data/.pids" 2>&1 | head -20
```

预期：全部存在，无 `No such file` 错误。

---

### Task 10: 模拟全新机器（删除预生成文件）

- [ ] **Step 1: 删除 .env / venv / node_modules / db**

```bash
cd "D:/portable-verify"
rm -f .env
rm -rf backend/.venv
rm -rf frontend/node_modules
rm -f data/repair_system.db*
```

Windows cmd：
```cmd
cd D:\portable-verify
del /f .env 2>nul
rd /s /q backend\.venv 2>nul
rd /s /q frontend\node_modules 2>nul
del /f data\repair_system.db* 2>nul
```

- [ ] **Step 2: 验证全清**

```bash
ls -la .env 2>&1 | head -1
ls backend/.venv 2>&1 | head -1
ls frontend/node_modules 2>&1 | head -1
ls data/repair_system.db 2>&1 | head -1
```

预期：全部「No such file or directory」。

---

### Task 11: 启动开发服务

- [ ] **Step 1: 双击 start.bat（或在 cmd 中运行）**

```bash
cd "D:/portable-verify"
cmd //c start.bat
```

或：
```cmd
cd D:\portable-verify
start.bat
```

预期 console 输出（节选）：
```
[start] 检查 Python ...
[start] 复制 .env.example 为 .env
[start] 创建 Python 虚拟环境 backend\.venv
[start] 初始化 SQLite 数据库
[init_db] 已创建默认管理员: admin / 123456
[start] 安装前端依赖（首次较慢）
[start] 启动 Flask + Vite ...
[start_dev] Flask 日志: D:\portable-verify\data\logs\flask.log
[start_dev] Vite  日志: D:\portable-verify\data\logs\vite.log
[start_dev] 浏览器打开 http://localhost:5173  (Ctrl+C 退出)
```

首次启动需要等 `pip install` 和 `npm install`（可能 2-5 分钟）。

- [ ] **Step 2: 验证 Flask + Vite 起来了**

另开一个终端：
```bash
curl -s http://localhost:5000/api/setup/status | head -50
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5173
```

预期：5000 端口返回 JSON（即使是 401/403）；5173 端口返回 `200`。

- [ ] **Step 3: 若启动失败**

查看日志：
```bash
cat "D:/portable-verify/data/logs/flask.log"
cat "D:/portable-verify/data/logs/vite.log"
```

| 错误 | 处理 |
|------|------|
| `python: command not found` | 让用户装 Python 3.11+，重启 start.bat |
| `pip install` 网络超时 | 重试，或换国内源（`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`） |
| `npm install` 失败 | 同上换源（`npm config set registry https://registry.npmmirror.com`） |
| Flask 端口被占 | `netstat -ano | findstr :5000`，杀掉占用进程 |
| `OperationalError: no such table` | 补 `backend/database/init.sql`（独立 fix commit） |
| 其他 | 记入任务备注 |

- [ ] **Step 4: 验证 admin/123456 可登录（API 级）**

```bash
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}' | head -200
```

预期：返回 JSON `{"code":200,"data":{"token":"..."}, ...}`。

- [ ] **Step 5: 浏览器手测（不可脚本化，必须人工）**

打开浏览器 `http://localhost:5173`：
- 看到登录页
- 输入 `admin` / `123456` → 点登录
- 跳到主页（仪表盘或商品列表等）

**这一步必须人工完成**，确认 UI 正常。若失败，记录浏览器 console 报错到任务备注。

---

### Task 12: 业务操作手测

- [ ] **Step 1: 建一个测试商品**

在 UI 中：商品管理 → 新增 → 名称「测试商品-verify」 → 售价 99 → 保存。

预期：列表里出现该商品，提示「创建成功」。

- [ ] **Step 2: 建一个测试工单**

工单管理 → 新增 → 类型「维修」 → 客户「散客」 → 设备描述「测试设备」 → 保存。

预期：列表里出现该工单，编号自增。

- [ ] **Step 3: API 级验证（用 curl 二次确认）**

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}' | python -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5000/api/products | python -c "import sys,json;d=json.load(sys.stdin);print('products count:', len(d.get('data',[])))"
```

预期：`products count: 1`（含刚才建的）。

- [ ] **Step 4: 关闭浏览器**

无需 stop.bat——验证下个任务要重启。

---

### Task 13: 重启验证持久化

- [ ] **Step 1: 停止服务**

在 `start.bat` 启动的 console 窗口里按 `Ctrl+C`，或在另一个 cmd 窗口运行：

```bash
cd "D:/portable-verify"
cmd //c stop.bat
```

预期：
```
[stop] 停止 Flask (pid=...)
[stop] 停止 Vite (pid=...)
[stop] 完成
```

- [ ] **Step 2: 验证端口已释放**

```bash
netstat -ano | findstr ":5000 " | findstr LISTENING
netstat -ano | findstr ":5173 " | findstr LISTENING
```

预期：无输出（两个端口都空闲）。

- [ ] **Step 3: 验证 db 文件仍在**

```bash
ls -la "D:/portable-verify/data/repair_system.db"*
```

预期：`repair_system.db` 文件存在（可能伴随 `-wal` / `-shm`）。

- [ ] **Step 4: 重新启动**

```bash
cd "D:/portable-verify"
cmd //c start.bat
```

预期：start.bat 检测到 `.env` / `.venv` / `node_modules` / `db` 都已存在，**跳过**首次初始化，直接启动服务。

- [ ] **Step 5: 浏览器验证数据还在**

打开 `http://localhost:5173`，登录 admin/123456，查看商品列表 / 工单列表：

预期：上一步建的「测试商品-verify」和测试工单**仍可见**。

- [ ] **Step 6: 停服（保持干净状态）**

```bash
cd "D:/portable-verify"
cmd //c stop.bat
```

---

### Task 14: 在干净目录跑 pytest（可选，但建议）

- [ ] **Step 1: 跑测试**

```bash
cd "D:/portable-verify/backend"
python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/pytest_verify.txt
```

预期：所有测试 PASS（同 Phase 1 结果一致）。

---

## Phase 4: archive 清理 + 文档收尾

### Task 15: 删除 docs/archive/ 目录

**Files:**
- Delete (git tracked): `docs/archive/docker-configs/`（整个目录）
- Delete (git tracked): `docs/archive/database_complete_v3.sql`

- [ ] **Step 1: 确认 archive 内容**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
ls docs/archive/
ls docs/archive/docker-configs/
```

预期：`docs/archive/` 下有 `docker-configs/` 和 `database_complete_v3.sql`。

- [ ] **Step 2: 检查是否还有代码引用 archive**

```bash
grep -rn "docs/archive" --include="*.py" --include="*.md" --include="*.bat" --include="*.sh" 2>/dev/null | grep -v "docs/archive/"
```

预期：无输出（README 里的引用将在 Task 16 删除）。

- [ ] **Step 3: git rm**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git rm -r docs/archive/docker-configs/
git rm docs/archive/database_complete_v3.sql
```

- [ ] **Step 4: commit**

```bash
git commit -m "$(cat <<'EOF'
chore: remove docs/archive/ (transitional Docker/MySQL reference)

2026-06-30 迁移时临时保留的 docker-compose 文件与 MySQL 原版 schema，
作为迁移期参考用途。本次验证完成后已无外部依赖，删除。

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### Task 16: 更新 README + VERSION.txt

**Files:**
- Modify: `README.md`（删除「归档清理」章节）
- Modify: `VERSION.txt`

- [ ] **Step 1: 删除 README 中的「归档清理」章节**

打开 `C:/Users/BruceZhao/Desktop/source-code/source-code/README.md`，**删除**以下整段：

```markdown
## 归档清理（2026-07-14 后执行）

两个过渡性目录将在 2 周后删除：
- `docs/archive/docker-configs/` —— 旧 docker 文件
- `docs/archive/database_complete_v3.sql` —— MySQL 原版 schema（参考用）

届时会再发一个 commit 完成清理。
```

位置：紧接「## 故障排查」章节之后，「## 技术支持」章节之前。

- [ ] **Step 2: 更新 VERSION.txt**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
echo "2026.07.03" > VERSION.txt
```

- [ ] **Step 3: 验证 README 渲染**

```bash
grep -n "归档清理" README.md
```

预期：无输出（章节已删除）。

- [ ] **Step 4: commit**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git add README.md VERSION.txt
git commit -m "$(cat <<'EOF'
docs: remove archive cleanup reminder; bump VERSION to 2026.07.03

archive/ 已在前一个 commit 删除，README 里的清理提醒同步移除。
版本号更新到本次收尾日期。

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

### Task 17: 最终验收

- [ ] **Step 1: 仓库状态干净**

```bash
cd "C:/Users/BruceZhao/Desktop/source-code/source-code"
git status --short
```

预期：无输出（除未跟踪的 `repair-system-portable-v2026.07.03.zip`，它已在 `.gitignore`）。

- [ ] **Step 2: __pycache__ 不再被跟踪**

```bash
git ls-files | grep "__pycache__" | wc -l
```

预期：`0`。

- [ ] **Step 3: 没有测试残留**

```bash
ls verify_bigint.db 2>&1 | head -1
ls backend/instance/ 2>&1 | head -1
```

预期：两个都「No such file or directory」。

- [ ] **Step 4: archive 已删**

```bash
ls docs/archive 2>&1 | head -1
```

预期：「No such file or directory」。

- [ ] **Step 5: 验证清单**

逐项确认（对应 spec 第 6 节）：

- [ ] `git status` 干净
- [ ] `__pycache__` 无一被跟踪
- [ ] `verify_bigint.db` 等测试残留已删除
- [ ] 干净目录解压 zip → `start.bat` → Flask + Vite 起来无报错
- [ ] `admin/123456` 登录成功
- [ ] 至少 1 个业务操作（建商品 / 建工单）成功
- [ ] `stop` + `start` 后数据持久化
- [ ] `pytest` 全部 PASS
- [ ] `docs/archive/` 已删除
- [ ] README 「归档清理」段已移除
- [ ] `VERSION.txt` = `2026.07.03`
- [ ] 全部 commit 信息符合 conventional commits 风格

- [ ] **Step 6: 清理临时验证目录（可选）**

```bash
rm -rf "D:/portable-verify"
```

---

## 完成清单

完成所有 17 个任务后，项目应处于：

1. ✅ 干净目录解压 zip → `start.bat` → 浏览器登录 → 跑通业务 → 重启数据持久化
2. ✅ 27 blueprint 全部通过测试
3. ✅ 仓库无 __pycache__ 跟踪、无测试残留
4. ✅ `docs/archive/` 已清理
5. ✅ README 反映最终状态
6. ✅ VERSION = 2026.07.03
7. ✅ 全部 commit 信息可读、可回滚