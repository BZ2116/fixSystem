# Portable Zip Verify & Wrap-up Design

**Date**: 2026-07-03
**Status**: Draft (pending user review)
**Scope**: 验证现有 portable zip 解压即用 + 收尾仓库状态。**不**新增功能、**不**改业务逻辑。

---

## 1. 背景与目标

`2026-06-30-portable-sqlite-migration` 计划的 25 个任务已全部 commit，`repair-system-portable-v2026.06.30.zip` 已生成。但：

- 仓库有 30+ `__pycache__` 文件被错误跟踪
- 20+ model 文件 + `config.py` / `security.py` / `auth.py` 显示 **uncommitted** 改动（性质待审）
- 一个 `backend/tests/test_jwt_revocation.py`（C1/C2 安全回归）untracked
- 测试残留（`verify_bigint.db`、`backend/instance/*.db`）散落
- **从未在干净机器上做端到端验证**：解压 → 启动 → 登录 → 跑业务 这条链路无实测

**目标**：清理仓库状态 + 验证 zip 解压即用 + 删除过渡性 archive 目录，让项目处于「可分发」状态。

## 2. 非目标

- 不动 27 个 blueprint 的业务逻辑
- 不重构 SQLite migration 已经完成的代码
- 不引入新依赖、不改技术栈

## 3. 设计

### 3.1 推进顺序（先清后验，每阶段一个 commit）

```
Phase 1: 仓库状态审计与清理  → commit "chore: tidy repo state"
Phase 2: 重打 zip           → 仅产出物，不需 commit
Phase 3: 端到端验证          → 发现的 bug 一个 fix 一个 commit
Phase 4: archive 清理 + 文档收尾 → commit "chore: archive cleanup"
```

### 3.2 Phase 1 — 仓库清理

**逐个审 uncommitted 改动**（`git diff` 逐文件看）：

| 文件 | 决策依据 | 预期动作 |
|------|----------|----------|
| `backend/app/config.py` | 应为 SQLite 迁移（移除 MySQL / 加 busy_timeout） | commit |
| `backend/app/security.py` | 应为 JWT 黑名单改 SQLite | commit |
| `backend/app/blueprints/auth.py` | 应为 cookie 配置（C2 修复配套） | commit |
| `backend/models/_base.py` | 应为 TimestampMixin | commit（如果还没） |
| 20+ model 文件 | 应为 SQLite 类型兼容（DECIMAL/JSON/BigInteger PK） | 按需要 commit 或 revert |
| `backend/tests/test_jwt_revocation.py` | untracked，C1/C2 安全回归 | commit 到 `backend/tests/` |
| `backend/instance/*.db` | 测试运行时生成 | **不**入库，`.gitignore` 补 `backend/instance/` |
| `__pycache__/**` | 已忽略但被跟踪了 | `git rm --cached -r` 摘出 |
| `verify_bigint.db`（根目录） | 临时验证产物 | `rm` 删除 |

**新增 `.gitignore` 条目**：
```
backend/instance/
```

**清理命令**：
```bash
# __pycache__ 摘出跟踪（保留本地）
git rm --cached -r backend/__pycache__ backend/app/__pycache__ ...  # 实际路径以 git ls-files 为准

# 测试残留
rm -f verify_bigint.db backend/instance/dev.db backend/instance/instance_smoke.db

# .gitignore 追加 + commit
```

### 3.3 Phase 2 — 重打 zip

直接用 `python build_portable.py`（已存在，跨平台版本）。

### 3.4 Phase 3 — 端到端验证

模拟目标机器的全新状态：

1. **准备干净目录**：例如 `D:\verify\`（或 `C:/temp/portable-verify/`）
2. **解压 zip** 到该目录
3. **删除模拟"首次运行"前不存在的文件**：
   - `.env`（让 start.bat 自动从 `.env.example` 复制）
   - `backend/.venv/`（让 pip install 重跑）
   - `frontend/node_modules/`（让 npm install 重跑）
   - `data/repair_system.db`（让 init_db.py 重新建）
4. **执行** `start.bat`
5. **观察日志** `data/logs/flask.log` 和 `vite.log` —— 确认无报错，端口 5000/5173 起来
6. **手测清单**：
   - 浏览器 `http://localhost:5173` → 登录页可见
   - `admin / 123456` 登录 → 跳主页
   - 建一个商品（商品管理 → 新增 → 提交）
   - 建一个工单（工单管理 → 新增 → 提交）
   - 关浏览器
7. **停服**：`stop.bat`
8. **重启**：`start.bat` → 再登录 → 查刚才的工单是否还在
9. **跑测试**：`cd backend && pytest -v`

**预期结果**：
- 全部 PASS（27 blueprint + smoke + utils + jwt_revocation）
- 端到端手测全部成功
- 数据持久化通过

**失败处理**：
- 若 `init_db.py` 报缺表 → 补 `backend/database/init.sql`，commit
- 若 blueprint 报 `no such table` → 同上
- 若 `build_portable.py` 漏关键文件 → 补 INCLUDE/EXCLUDE 规则，commit
- 若 BigInteger PK 不自增（已知 SQLite 限制） → 修 model，commit

### 3.5 Phase 4 — archive 清理

README 里写了「归档清理（2026-07-14 后执行）」，今天 7/3 已过期（虽然 7/14 还没到，但开发节奏已经走到这一步）。

**执行**：
```bash
git rm -r docs/archive/docker-configs/ docs/archive/database_complete_v3.sql
```

**README 修改**：
- 删除「归档清理」章节

**VERSION.txt**：更新为 `2026.07.03`

## 4. 测试策略

- **自动化**：`backend/tests/` 现有 5 个测试文件（conftest / smoke / utils / blueprints / jwt_revocation），全部跑过
- **手测**：见 3.4 第 6 步

## 5. 风险

| 风险 | 应对 |
|------|------|
| Phase 3 验证发现阻塞性 bug | 中断回滚，按 bug 类型单独立 fix commit |
| Windows 路径权限问题 | 用 `D:\verify\` 而非 `C:\` |
| pytest 失败但功能 OK | 记录但优先保证功能跑通 |
| network / npm 慢 | 提前预热 `npm install` 缓存 |

## 6. 验收标准

- [ ] `git status` 干净（除预期内的改动）
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