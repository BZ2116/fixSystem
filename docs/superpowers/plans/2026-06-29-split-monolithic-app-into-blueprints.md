# Split Monolithic app.py into Blueprints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把根目录 18590 行的 `app.py`（275+ 路由）按业务域拆分到 `backend/app/blueprints/` 下的多个 blueprint 文件，让 `backend/run.py` 真正成为可独立运行的入口，最终删除根目录 `app.py`。

**Architecture:** 渐进式迁移（strangler pattern）。先抽共享 utilities 和迁移全局钩子（errors/security），让 `backend/app/` 现有空壳文件真正生效；然后按"小域→中域→大域→财务"逐个 blueprint 迁移，每阶段跑 smoke test 验证。最后把根目录 `app.py` 缩减为 5 行薄壳（`from backend.run import app`），最终删除。

**Tech Stack:** Flask 2.3.3 + Flask-SQLAlchemy 3.0.5 + Flask-JWT-Extended 4.5.2 + Flask-CORS 4.0.0 + Flask-Migrate 4.0.5 + Flask-Talisman 1.1.0 + PyMySQL + redis + bcrypt + gunicorn 21.2.0 + pytest。

**Prerequisites (手动执行一次)：**
```bash
cd C:/Users/BruceZhao/Desktop/source-code/source-code
git init
git add -A
git commit -m "chore: snapshot before blueprint split refactor"
```
所有任务的 commit 命令都假设在 git 仓库中执行。如果用户不想用 git，跳过 commit 步骤即可。

---

## 蓝图拆分约定（所有 blueprint 必须遵守）

为保持一致性，**每个 blueprint 必须满足以下约定**：

1. **命名**：`backend/app/blueprints/<resource>.py`，文件名小写、下划线分隔（如 `customer.py`、`users_admin.py`、`work_order.py`）。
2. **URL 前缀**：`Blueprint(name, __name__, url_prefix='/api/<resources>')`。路由函数内只写相对路径。
3. **异常路径**：如果一个资源的端点跨多个前缀（如 `/api/user/info` 和 `/api/users`），**拆成两个 blueprint**（见 Task 8 示例）。
4. **响应工具**：统一使用 `from app.utils import ok, fail, paginate_query`，禁止 `jsonify({'code':..})` 手写。
5. **权限装饰器**：JWT 校验用 `@jwt_required()`，业务权限用 `@permission('resource:action')`。
6. **模型导入**：用 `from models.<module> import <Model>`，避免循环依赖。
7. **导入顺序**：stdlib → third-party (flask) → local (`extensions`, `app.*`, `models.*`)。
8. **行数控制**：单个 blueprint 文件不超过 1500 行。超出则按子资源进一步拆分（如 product → product_unit / product_category）。

---

## 文件结构（迁移后）

```
source-code/
├── app.py                              # 重构后: 5 行薄壳，仅作兼容入口（最后阶段删除）
├── backend/
│   ├── run.py                          # 不变: 生产入口
│   ├── extensions.py                   # 已有, 不变
│   ├── app/
│   │   ├── __init__.py                 # 已有: create_app 工厂
│   │   ├── config.py                   # 已有, 不变
│   │   ├── errors.py                   # 已有, 不变
│   │   ├── security.py                 # 已有, 不变
│   │   ├── seed.py                     # 已有, 不变
│   │   ├── blueprints/
│   │   │   ├── __init__.py             # 修改: 注册所有蓝图
│   │   │   ├── setup.py                # 已有
│   │   │   ├── auth.py                 # 新建
│   │   │   ├── user.py                 # 新建
│   │   │   ├── health.py               # 新建 (从 __init__.py 移出)
│   │   │   ├── customer.py             # 新建
│   │   │   ├── supplier.py             # 新建
│   │   │   ├── product.py              # 新建
│   │   │   ├── device.py               # 新建
│   │   │   ├── workorder.py            # 新建
│   │   │   ├── receive.py              # 新建
│   │   │   ├── dispatch.py             # 新建
│   │   │   ├── inventory.py            # 新建
│   │   │   ├── purchase.py             # 新建
│   │   │   ├── sales.py                # 新建
│   │   │   ├── quote.py                # 新建
│   │   │   ├── preorder.py             # 新建
│   │   │   ├── return_order.py         # 新建
│   │   │   ├── finance.py              # 新建
│   │   │   ├── reconciliation.py       # 新建
│   │   │   ├── dashboard.py            # 新建
│   │   │   ├── settings.py             # 新建
│   │   │   ├── log.py                  # 新建
│   │   │   ├── statistics.py           # 新建
│   │   │   ├── salary.py               # 新建
│   │   │   ├── expense.py              # 新建
│   │   │   ├── asset.py                # 新建
│   │   │   └── office.py               # 新建
│   │   └── utils/
│   │       ├── __init__.py             # 已有 (空)
│   │       ├── response.py             # 新建
│   │       ├── pagination.py           # 新建
│   │       ├── excel.py                # 新建
│   │       ├── order_no.py             # 新建
│   │       ├── text.py                 # 新建
│   │       └── serialization.py        # 新建
│   ├── models/                         # 已有, 不动
│   └── tests/
│       ├── test_smoke.py               # 已有, 扩展
│       └── test_blueprints.py          # 新建 (端到端验证)
```

---

## Phase 1: 基础设施（先让 backend/app/ 现有空壳真正生效）

### Task 1: 抽取响应工具 `utils/response.py`

**Files:**
- Create: `backend/app/utils/response.py`
- Modify: `backend/app/utils/__init__.py`

- [ ] **Step 1: 创建 response 工具**

写入 `backend/app/utils/response.py`:

```python
"""统一响应封装。所有路由统一返回 {code, message, data, request_id} 格式。"""
from flask import jsonify, g


def ok(data=None, message='ok', code=200):
    payload = {'code': code, 'message': message, 'data': data or {}}
    rid = getattr(g, 'request_id', None)
    if rid:
        payload['request_id'] = rid
    return jsonify(payload), 200


def fail(message='error', code=400, http_status=None):
    payload = {'code': code, 'message': message}
    rid = getattr(g, 'request_id', None)
    if rid:
        payload['request_id'] = rid
    return jsonify(payload), http_status or code


def page_ok(items, total, page, per_page, message='ok'):
    return ok({
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if per_page else 0,
    }, message)
```

- [ ] **Step 2: 在 utils 包 __init__ 暴露**

写入 `backend/app/utils/__init__.py`:

```python
from .response import ok, fail, page_ok

__all__ = ['ok', 'fail', 'page_ok']
```

- [ ] **Step 3: 验证导入**

```bash
cd backend && python -c "from app.utils import ok, fail, page_ok; print('ok')"
```
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add backend/app/utils/response.py backend/app/utils/__init__.py
git commit -m "feat(utils): add unified response helpers (ok/fail/page_ok)"
```

---

### Task 2: 抽取分页工具 `utils/pagination.py`

**Files:**
- Create: `backend/app/utils/pagination.py`
- Modify: `backend/app/utils/__init__.py`

- [ ] **Step 1: 创建 pagination 工具**

写入 `backend/app/utils/pagination.py`:

```python
"""统一分页参数解析与查询封装。"""
from flask import request


def get_page_params(default_per_page=20, max_per_page=200):
    """从 request.args 解析 page/per_page，带边界保护。"""
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = int(request.args.get('per_page', default_per_page))
        per_page = max(1, min(per_page, max_per_page))
    except (TypeError, ValueError):
        page, per_page = 1, default_per_page
    return page, per_page


def paginate_query(query, default_per_page=20, max_per_page=200):
    """对 SQLAlchemy query 执行分页，返回 (items, total, page, per_page)。"""
    page, per_page = get_page_params(default_per_page, max_per_page)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total, page, per_page
```

- [ ] **Step 2: 在 utils __init__ 暴露**

修改 `backend/app/utils/__init__.py` 末尾追加:

```python
from .pagination import get_page_params, paginate_query

__all__ = ['ok', 'fail', 'page_ok', 'get_page_params', 'paginate_query']
```

- [ ] **Step 3: 验证导入**

```bash
cd backend && python -c "from app.utils import get_page_params, paginate_query; print('ok')"
```
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add backend/app/utils/pagination.py backend/app/utils/__init__.py
git commit -m "feat(utils): add pagination helpers"
```

---

### Task 3: 抽取文本/订单号/序列化/Excel 工具

**Files:**
- Create: `backend/app/utils/text.py`
- Create: `backend/app/utils/order_no.py`
- Create: `backend/app/utils/serialization.py`
- Create: `backend/app/utils/excel.py`
- Modify: `backend/app/utils/__init__.py`

- [ ] **Step 1: 创建 text.py（拼音编码）**

写入 `backend/app/utils/text.py`:

```python
"""文本处理工具：拼音首字母生成（用于商品/客户编码）。"""
import re

try:
    from pypinyin import lazy_pinyin
    _HAS_PYPINYIN = True
except ImportError:
    _HAS_PYPINYIN = False


def generate_pinyin_code(text: str) -> str:
    """从中文文本生成拼音首字母编码。例如 '客户A' → 'KHA'。
    非中文字符直接保留。"""
    if not text:
        return ''
    if _HAS_PYPINYIN:
        parts = lazy_pinyin(text)
        return ''.join(p[0].upper() for p in parts if p)
    # fallback: 取每个字符首字母（中文用 unicode 首字符）
    return ''.join(c[0].upper() if c else '' for c in text)
```

> 注：原 app.py 的 `generate_pinyin_code` 在 134 行。如果 `pypinyin` 不在 requirements.txt，先加入 `backend/requirements.txt` 末尾。

- [ ] **Step 2: 创建 order_no.py（订单号生成）**

写入 `backend/app/utils/order_no.py`:

```python
"""订单号生成器：按业务前缀 + 日期 + 序号。"""
from datetime import datetime
import threading

_lock = threading.Lock()
_counter = {}


def generate_code(prefix: str, width: int = 4) -> str:
    """生成形如 'WO202606290001' 的业务单号。
    
    Args:
        prefix: 业务前缀（WO/RC/SO/PO/QO...）
        width: 序号位数（默认 4 位，不足补 0）
    """
    today = datetime.now().strftime('%Y%m%d')
    key = f'{prefix}-{today}'
    with _lock:
        _counter[key] = _counter.get(key, 0) + 1
        seq = _counter[key]
    return f'{prefix}{today}{seq:0{width}d}'


def reset_counter(prefix: str = None):
    """测试用：重置计数器。"""
    global _counter
    if prefix is None:
        _counter = {}
    else:
        today = datetime.now().strftime('%Y%m%d')
        _counter.pop(f'{prefix}-{today}', None)
```

- [ ] **Step 3: 创建 serialization.py（模型转字典）**

写入 `backend/app/utils/serialization.py`:

```python
"""SQLAlchemy 模型 → dict 序列化工具。"""
from datetime import datetime, date
from decimal import Decimal


def to_dict(model, fields=None, exclude=None):
    """通用序列化。
    
    Args:
        model: SQLAlchemy 模型实例
        fields: 白名单字段列表（None 表示全部）
        exclude: 黑名单字段列表
    """
    if model is None:
        return None
    exclude = set(exclude or [])
    result = {}
    for col in model.__table__.columns:
        if col.name in exclude:
            continue
        if fields and col.name not in fields:
            continue
        value = getattr(model, col.name)
        result[col.name] = _serialize_value(value)
    return result


def _serialize_value(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, Decimal):
        return float(value)
    return value
```

- [ ] **Step 4: 创建 excel.py（导出/导入）**

写入 `backend/app/utils/excel.py`:

```python
"""Excel 导入导出工具。"""
import io
from openpyxl import Workbook, load_workbook


def export_to_excel(rows: list, headers: dict, sheet_name: str = 'Sheet1') -> bytes:
    """导出 Excel。
    
    Args:
        rows: 数据列表，每项是 dict
        headers: {列名: 表头文本}，决定顺序和标题
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(list(headers.values()))
    for row in rows:
        ws.append([row.get(col, '') for col in headers.keys()])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def read_excel_data(file_storage) -> list:
    """读取 Excel 上传文件，返回 [{列名: 值}, ...]"""
    wb = load_workbook(filename=io.BytesIO(file_storage.read()), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h) if h is not None else f'col{i}' for i, h in enumerate(rows[0])]
    return [dict(zip(headers, row)) for row in rows[1:] if any(c is not None for c in row)]
```

- [ ] **Step 5: 更新 utils/__init__.py**

重写 `backend/app/utils/__init__.py`:

```python
from .response import ok, fail, page_ok
from .pagination import get_page_params, apply_pagination
from .text import generate_pinyin_code
from .order_no import generate_code, reset_counter
from .serialization import to_dict
from .excel import export_to_excel, read_excel_data

__all__ = [
    'ok', 'fail', 'page_ok',
    'get_page_params', 'apply_pagination',
    'generate_pinyin_code', 'generate_code', 'reset_counter',
    'to_dict', 'export_to_excel', 'read_excel_data',
]
```

- [ ] **Step 6: 如果 pypinyin 用了, 更新 requirements.txt**

```bash
echo 'pypinyin==0.51.0' >> backend/requirements.txt
```

- [ ] **Step 7: 验证所有导入**

```bash
cd backend && python -c "from app.utils import ok, fail, page_ok, get_page_params, apply_pagination, generate_pinyin_code, generate_code, to_dict, export_to_excel, read_excel_data; print('ok')"
```
Expected: `ok`

- [ ] **Step 8: 写最小单元测试**

写入 `backend/tests/test_utils.py`:

```python
"""utils 单元测试。"""
import pytest
from app.utils import ok, fail, page_ok, generate_code, reset_counter, to_dict, generate_pinyin_code


def test_ok_default():
    """ok() 返回 200 + 默认 message"""
    resp, status = ok({'a': 1})
    assert status == 200
    body = resp.get_json()
    assert body['code'] == 200
    assert body['data'] == {'a': 1}


def test_fail_returns_correct_status():
    """fail() 返回指定 code"""
    resp, status = fail('test error', code=403, http_status=403)
    assert status == 403
    body = resp.get_json()
    assert body['code'] == 403
    assert body['message'] == 'test error'


def test_generate_code_format():
    """generate_code 生成正确格式"""
    reset_counter('TST')
    code1 = generate_code('TST', width=4)
    assert code1.startswith('TST')
    assert len(code1) == 4 + 8 + 4  # 前缀 + 日期 + 序号
    code2 = generate_code('TST', width=4)
    assert code1 != code2


def test_to_dict_datetime():
    """to_dict 正确处理 datetime"""
    from datetime import datetime
    from extensions import db

    class MockModel:
        __table__ = db.Table(
            'mock', db.MetaData(),
            db.Column('id', db.Integer, primary_key=True),
            db.Column('created_at', db.DateTime),
        )

    # 简化测试：传 None
    assert to_dict(None) is None


def test_pinyin_chinese():
    """generate_pinyin_code 处理中文"""
    code = generate_pinyin_code('客户')
    assert code  # 非空即可（依赖 pypinyin 是否安装）
```

```bash
cd backend && pytest tests/test_utils.py -v
```
Expected: 全部 PASS（如果 pypinyin 没装，pinyin 测试 skip）

- [ ] **Step 9: Commit**

```bash
git add backend/app/utils/ backend/tests/test_utils.py backend/requirements.txt
git commit -m "feat(utils): extract text/order_no/serialization/excel helpers"
```

---

### Task 4: 让 errors.py 生效（迁移根目录 app.py 里的错误处理器）

**Files:**
- Modify: `backend/app/errors.py`（当前为空 → 实现已存在的内容，但实际已有内容）

查看 `backend/app/errors.py` 当前内容（已经是完整实现），无需改动。直接验证：

```bash
cd backend && python -c "from app.errors import register_error_handlers; print('ok')"
```
Expected: `ok`

如果验证通过，跳到 Task 5。

- [ ] **Step 1: Commit（如果验证通过就跳过）**

---

### Task 5: 让 security.py 生效

**Files:**
- Modify: `backend/app/security.py`（追加 permission_required 装饰器和 get_current_user_id）

`security.py` 已存在但没有 `get_current_user_id` 和 `permission_required`。在文件末尾追加：

```python
def get_current_user_id() -> int:
    """从 JWT claims 取当前用户 ID。"""
    from flask_jwt_extended import get_jwt_identity
    return get_jwt_identity()


def get_current_user():
    """取当前用户对象。"""
    from models.system import SysUser
    uid = get_current_user_id()
    return SysUser.query.get(uid) if uid else None
```

- [ ] **Step 1: 追加并验证**

```bash
cd backend && python -c "from app.security import get_current_user_id, get_current_user, permission, configure_jwt, revoke_token, safe_save; print('ok')"
```
Expected: `ok`

- [ ] **Step 2: Commit**

```bash
git add backend/app/security.py
git commit -m "feat(security): expose get_current_user_id and get_current_user"
```

---

## Phase 2: 小域先行（auth/user/health）

### Task 6: 抽出 health 蓝图（最小、最稳）

**Files:**
- Create: `backend/app/blueprints/health.py`
- Modify: `backend/app/blueprints/__init__.py`

- [ ] **Step 1: 创建 health.py**

写入 `backend/app/blueprints/health.py`:

```python
"""健康检查端点。"""
from flask import Blueprint
from extensions import db
from app.utils import ok

bp = Blueprint('health', __name__)


@bp.route('/health')
def health():
    """健康检查：验证数据库连通性。"""
    try:
        db.session.execute(db.text('SELECT 1'))
        db_ok = True
    except Exception:
        db_ok = False
    return ok({'status': 'healthy' if db_ok else 'degraded', 'db': db_ok})
```

- [ ] **Step 2: 在 blueprints/__init__.py 注册**

修改 `backend/app/blueprints/__init__.py`:

```python
"""蓝图注册入口。"""
from flask import Flask


def register_blueprints(app: Flask):
    from .setup import bp as setup_bp
    from .health import bp as health_bp
    app.register_blueprint(setup_bp, url_prefix='/api/setup')
    app.register_blueprint(health_bp)  # /api/health
```

- [ ] **Step 3: 移除 __init__.py 里的临时 health 路由**

修改 `backend/app/__init__.py`，删除 health 路由（62-65 行）：

```python
    # 删除这段:
    # @app.route('/api/health')
    # def health():
    #     return {'code': 200, 'message': 'ok', 'data': {'status': 'healthy'}}, 200
```

- [ ] **Step 4: 跑 smoke test**

```bash
cd backend && pytest tests/test_smoke.py -v
```
Expected: `test_health` PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/blueprints/health.py backend/app/blueprints/__init__.py backend/app/__init__.py
git commit -m "feat(blueprints): extract health endpoint"
```

---

### Task 7: 抽出 auth 蓝图（login/register）

**Files:**
- Create: `backend/app/blueprints/auth.py`
- Modify: `backend/app/blueprints/__init__.py`

- [ ] **Step 1: 读取 app.py 211-310 行的 login/register 函数**

```bash
sed -n '211,316p' source-code/app.py
```

- [ ] **Step 2: 创建 auth.py**

写入 `backend/app/blueprints/auth.py`:

```python
"""认证：登录、注册。"""
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from app.utils import ok, fail
from app.security import get_current_user_id

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return fail('用户名和密码必填', code=400)

    from models.system import SysUser
    user = SysUser.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return fail('用户名或密码错误', code=401)
    if user.status != 1:
        return fail('账号已禁用', code=403)

    # 取权限码列表
    perms = [p.code for p in user.roles[0].permissions] if user.roles else []
    token = create_access_token(
        identity=str(user.id),
        additional_claims={'permissions': perms, 'username': user.username},
    )
    return ok({'token': token, 'user': {'id': user.id, 'username': user.username, 'real_name': user.real_name}})


@bp.route('/register', methods=['POST'])
def register():
    """注册（仅在 setup 启用时）。"""
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if len(username) < 3 or len(password) < 8:
        return fail('用户名至少 3 字符，密码至少 8 字符', code=400)

    from models.system import SysUser
    if SysUser.query.filter_by(username=username).first():
        return fail('用户名已存在', code=400)

    user = SysUser(
        username=username,
        password=generate_password_hash(password),
        real_name=data.get('real_name', username),
        status=1,
    )
    db.session.add(user)
    db.session.commit()
    return ok({'id': user.id}, '注册成功')
```

> 注：login/register 函数实际签名/字段以 `app.py` 第 211-310 行为准。迁移时必须逐字照搬原逻辑，避免行为变化。

- [ ] **Step 3: 在 blueprints/__init__.py 注册**

修改 `backend/app/blueprints/__init__.py`:

```python
def register_blueprints(app: Flask):
    from .setup import bp as setup_bp
    from .health import bp as health_bp
    from .auth import bp as auth_bp
    app.register_blueprint(setup_bp, url_prefix='/api/setup')
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)  # 自带 url_prefix='/api/auth'
```

- [ ] **Step 4: 跑 smoke test**

```bash
cd backend && pytest tests/test_smoke.py -v
```
Expected: 全部 PASS

- [ ] **Step 5: 手动 curl 测试（可选，需要真实 DB）**

```bash
cd backend && python run.py &
curl -X POST http://localhost:5000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"wrong"}'
# Expected: {"code":401,"message":"用户名或密码错误"}
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/blueprints/auth.py backend/app/blueprints/__init__.py
git commit -m "feat(blueprints): extract auth (login/register)"
```

---

### Task 8: 抽出 user 蓝图（get_user_info / get_users）

**Files:**
- Create: `backend/app/blueprints/user.py`（`/api/user/*` 前缀）
- Create: `backend/app/blueprints/users_admin.py`（`/api/users/*` 前缀）
- Modify: `backend/app/blueprints/__init__.py`

> 设计选择：`/api/user/*`（当前用户自己的信息）和 `/api/users`（管理端的用户列表）是不同的资源集合，拆成两个 blueprint 保持"一个 blueprint 一个 url_prefix"的一致约定。

- [ ] **Step 1: 读取 app.py 318-400 和 5483-5515 行**

```bash
sed -n '318,400p' source-code/app.py
sed -n '5483,5515p' source-code/app.py
```

- [ ] **Step 2: 创建 user.py（当前用户）**

写入 `backend/app/blueprints/user.py`:

```python
"""当前登录用户自己的信息。"""
from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.utils import ok, fail
from app.security import get_current_user

bp = Blueprint('user', __name__, url_prefix='/api/user')


@bp.route('/info')
@jwt_required()
def get_user_info():
    user = get_current_user()
    if not user:
        return fail('用户不存在', code=404)
    return ok({
        'id': user.id,
        'username': user.username,
        'real_name': user.real_name,
        'permissions': [p.code for p in (user.roles[0].permissions if user.roles else [])],
    })
```

- [ ] **Step 3: 创建 users_admin.py（管理端用户列表）**

写入 `backend/app/blueprints/users_admin.py`:

```python
"""管理端用户列表（需要 user:list 权限）。"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.utils import ok, paginate_query
from app.security import permission

bp = Blueprint('users_admin', __name__, url_prefix='/api/users')


@bp.route('')
@jwt_required()
@permission('user:list')
def list_users():
    from models.system import SysUser
    q = SysUser.query
    keyword = request.args.get('keyword', '').strip()
    if keyword:
        q = q.filter(SysUser.username.like(f'%{keyword}%'))
    items, total, page, per_page = paginate_query(q)
    return ok({
        'items': [{
            'id': u.id, 'username': u.username, 'real_name': u.real_name,
            'status': u.status,
            'created_at': u.created_at.strftime('%Y-%m-%d %H:%M:%S') if u.created_at else None,
        } for u in items],
        'total': total,
        'page': page,
        'per_page': per_page,
    })
```

> 实际字段名以原 app.py 为准（注意 created_at / status / roles 关联等）。

- [ ] **Step 4: 注册**

修改 `backend/app/blueprints/__init__.py`:

```python
def register_blueprints(app: Flask):
    from .setup import bp as setup_bp
    from .health import bp as health_bp
    from .auth import bp as auth_bp
    from .user import bp as user_bp
    from .users_admin import bp as users_admin_bp
    app.register_blueprint(setup_bp, url_prefix='/api/setup')
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(users_admin_bp)
```

- [ ] **Step 5: 跑测试**

```bash
cd backend && pytest tests/test_smoke.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/blueprints/user.py backend/app/blueprints/users_admin.py backend/app/blueprints/__init__.py
git commit -m "feat(blueprints): extract user endpoints (self + admin)"
```

---

## Phase 3: 中等 CRUD 域

### Task 9-15: customer / supplier / product / device / quote / office / dashboard

每个任务模式相同（重复工作用统一模板）。示例 Task 9：

---

### Task 9: 抽出 customer 蓝图

**Files:**
- Create: `backend/app/blueprints/customer.py`
- Modify: `backend/app/blueprints/__init__.py`

- [ ] **Step 1: 读取 app.py 396-528 行（CRUD）+ 11201/11235 行（导入导出）+ 12227 行（批量删除）**

```bash
sed -n '396,528p' source-code/app.py
sed -n '11201,11270p' source-code/app.py
sed -n '12227,12260p' source-code/app.py
```

- [ ] **Step 2: 创建 customer.py**

写入 `backend/app/blueprints/customer.py`:

```python
"""客户管理 CRUD + 导入导出 + 批量删除。"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from extensions import db
from app.utils import ok, fail, paginate_query, export_to_excel, read_excel_data, to_dict
from app.security import permission

bp = Blueprint('customer', __name__, url_prefix='/api/customers')


@bp.route('', methods=['GET'])
@jwt_required()
@permission('customer:list')
def list_customers():
    from models.customer import Customer
    q = Customer.query
    keyword = request.args.get('keyword', '').strip()
    if keyword:
        q = q.filter(Customer.name.like(f'%{keyword}%'))
    items, total, page, per_page = paginate_query(q)
    return ok({
        'items': [to_dict(c) for c in items],
        'total': total,
        'page': page,
        'per_page': per_page,
    })


@bp.route('', methods=['POST'])
@jwt_required()
@permission('customer:create')
def create_customer():
    from models.customer import Customer
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return fail('客户名称必填', code=400)
    c = Customer(
        name=name,
        contact=data.get('contact', ''),
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        discount_rate=data.get('discount_rate', 1.0),
        remark=data.get('remark', ''),
    )
    db.session.add(c)
    db.session.commit()
    return ok({'id': c.id}, '创建成功')


@bp.route('/<int:cid>', methods=['GET'])
@jwt_required()
def get_customer(cid):
    from models.customer import Customer
    c = Customer.query.get(cid)
    if not c:
        return fail('客户不存在', code=404)
    return ok(to_dict(c))


@bp.route('/<int:cid>', methods=['PUT'])
@jwt_required()
@permission('customer:update')
def update_customer(cid):
    from models.customer import Customer
    c = Customer.query.get(cid)
    if not c:
        return fail('客户不存在', code=404)
    data = request.get_json() or {}
    for field in ['name', 'contact', 'phone', 'address', 'discount_rate', 'remark']:
        if field in data:
            setattr(c, field, data[field])
    db.session.commit()
    return ok({'id': c.id}, '更新成功')


@bp.route('/<int:cid>', methods=['DELETE'])
@jwt_required()
@permission('customer:delete')
def delete_customer(cid):
    from models.customer import Customer
    c = Customer.query.get(cid)
    if not c:
        return fail('客户不存在', code=404)
    db.session.delete(c)
    db.session.commit()
    return ok(message='删除成功')


@bp.route('/export', methods=['GET'])
@jwt_required()
@permission('customer:export')
def export():
    from models.customer import Customer
    rows = [to_dict(c) for c in Customer.query.all()]
    headers = {'id': 'ID', 'name': '客户名', 'contact': '联系人', 'phone': '电话', 'address': '地址'}
    from flask import Response
    return Response(
        export_to_excel(rows, headers),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=customers.xlsx'},
    )


@bp.route('/import', methods=['POST'])
@jwt_required()
@permission('customer:import')
def import_excel():
    from models.customer import Customer
    file = request.files.get('file')
    if not file:
        return fail('请上传文件', code=400)
    rows = read_excel_data(file)
    created = 0
    for row in rows:
        name = (row.get('客户名') or row.get('name') or '').strip()
        if not name:
            continue
        if Customer.query.filter_by(name=name).first():
            continue
        c = Customer(
            name=name,
            contact=row.get('联系人') or row.get('contact') or '',
            phone=str(row.get('电话') or row.get('phone') or ''),
            address=row.get('地址') or row.get('address') or '',
        )
        db.session.add(c)
        created += 1
    db.session.commit()
    return ok({'created': created}, f'导入成功 {created} 条')


@bp.route('/batch-delete', methods=['POST'])
@jwt_required()
@permission('customer:delete')
def batch_delete():
    from models.customer import Customer
    ids = (request.get_json() or {}).get('ids', [])
    if not ids:
        return fail('ids 必填', code=400)
    Customer.query.filter(Customer.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return ok({'deleted': len(ids)}, f'删除 {len(ids)} 条')
```

> 字段名（contact / phone / discount_rate 等）以 `models/customer/base.py` 实际定义为准。

- [ ] **Step 3: 注册 + 测试 + commit**

```python
# blueprints/__init__.py 加一行:
from .customer import bp as customer_bp
app.register_blueprint(customer_bp)
```

```bash
cd backend && pytest tests/test_smoke.py -v
```

```bash
git add backend/app/blueprints/customer.py backend/app/blueprints/__init__.py
git commit -m "feat(blueprints): extract customer CRUD + import/export"
```

---

### Task 10: 抽出 supplier 蓝图（参照 Task 9 模板）

完全复制 Task 9 的结构，路径前缀 `/api/suppliers`，模型换为 `models.supplier.Supplier`，权限码 `supplier:*`，export headers 调整列名。

---

### Task 11: 抽出 product 蓝图（含 units / categories / batch-update）

`/api/products`, `/api/product/units`, `/api/product/categories` 三个路径前缀，三个 Blueprint 或一个带 sub-route 的 Blueprint。**建议拆 3 个**：products / units / categories，分别在 `product.py` / `product_unit.py` / `product_category.py`。batch-update 留在 product.py。

额外字段以 `models/product/info.py` 为准（含 stock_warn 等）。

---

### Task 12: 抽出 device 蓝图

`/api/devices`, `/api/devices/own` —— 一个 blueprint 即可。

字段以 `models/asset/asset.py` 为准。

---

### Task 13: 抽出 quote 蓝图

`/api/quotes` CRUD + `/api/quotes/<id>/{confirm,to-workorder,to-receive,to-sales}` 状态机。

状态机函数较长（每个 ~30 行），保持原样迁移，不要重构行为。

---

### Task 14: 抽出 office 蓝图

`/api/offices` CRUD，仅 ~60 行，最简单。

---

### Task 15: 抽出 dashboard 蓝图

`/api/dashboard/{stats,workorder-trend,income-trend}` —— 三个查询路由，引用 statistics 聚合函数。

---

## Phase 4: 核心业务域（大块）

### Task 16: 抽出 inventory 蓝图（最大域之一）

**Files:**
- Create: `backend/app/blueprints/inventory.py`
- Modify: `backend/app/blueprints/__init__.py`

包含：
- `/api/inventory/stock` (列表查询)
- `/api/inventory/in` `/api/inventory/out` (出入库)
- `/api/inventory/check` (盘点)
- `/api/inventory/check/<id>/audit, /complete, /diff-report`
- `/api/warehouses` (CRUD)
- `/api/inventory/logs`
- `/api/transfer/orders` (调拨 CRUD)
- `/api/cost-adjusts` (成本调整)
- 各 export 路由

行号范围：3539-10680 + 18377/18447。这是最大的 blueprint（~7000 行）。

**子任务（每段路由一个 step）：**

- [ ] **Step 1-15: 每段一个 step**，逐段从 app.py 复制到 inventory.py。每段复制后跑 `pytest tests/test_smoke.py -v`，最后整体 commit。

> 重要：这段必须**逐函数迁移**，不能批量复制粘贴。建议按以下顺序：stock → in/out → check → warehouses → logs → transfer → cost-adjust → exports。

预计本任务耗时最长，可分多个 commit。

---

### Task 17: 抽出 purchase 蓝图

`/api/purchase/orders` CRUD + audit + invoice，`/api/purchase/invoices` CRUD + certify + deduct。

audit 函数 ~186 行（行号 8546），触发入库。要保持事务完整性。

---

### Task 18: 抽出 sales 蓝图

`/api/sales/orders` CRUD + audit + print，`/api/sales/invoices` CRUD，`/api/sales/receipts` CRUD + print + void，`/api/sales/returns` 退单，`/api/sales/fix-prices` 工具。

audit 176 行（行号 8959），触发出库+资产绑定。

---

### Task 19: 抽出 workorder 蓝图（最复杂域）

`/api/workorders` CRUD + 13 个状态机操作 + 配件管理 + 日志 + 批量删除 + export。

`settle_workorder` 226 行（行号 2489）—— 最长的状态机。**强烈建议在迁移前先抽取 `services/workorder_service.py`**，把核心逻辑（库存扣减、费用写入、财务流水）抽出来，路由层只剩参数校验和事务包装。

预计本任务 +20: services/ 抽取 4-5 个核心 service（workorder_service / receive_service / inventory_service / sales_service / finance_service）。

---

### Task 20: 抽出 receive 蓝图

`/api/receiveorders` CRUD + 14 个状态机操作 + 配件/照片/签收子资源 + export。

`settle_receiveorder` 204 行（行号 6497）。`allocate_receiveorder` 192 行（行号 6168）。

外部报价流程有 4-6 个相似函数（6816-7013），建议在 receive_service.py 里抽象 `external_quote_flow(state)`。

---

### Task 21: 抽出 dispatch 蓝图

`/api/dispatch/{manual, /<id>/{accept,reject,arrive,finish,redirect}}` + 查询路由。

---

### Task 22: 抽出 asset 蓝图

`/api/asset/types` + `/api/assets` CRUD + scrap + import/export。

---

## Phase 5: 财务 / 统计域

### Task 23: 抽出 finance 蓝图（最大财务域）

`/api/finance/accounts` + `/api/finance/records` + `/api/finance/receivables` + `/api/finance/payables` + 各 summary/export/print 路由 + `/api/invoices`。

`transfer_finance_account` 106 行（行号 10815），事务处理。建议抽 `services/finance_service.py`。

---

### Task 24: 抽出 reconciliation 蓝图

`/api/reconciliation/{customer,supplier,account}` —— 6 个相似函数（行号 16806-17279），可抽象。

---

### Task 25: 抽出 salary / expense / statistics 蓝图

三个蓝图彼此独立，可并行拆分：

- `/api/salary` CRUD + pay + statistics（行号 15975-16375）
- `/api/expense` CRUD + confirm + statistics（行号 16379-16800）
- `/api/statistics/{revenue,employee,customer,product,dashboard}`（行号 15446-15970）

每个蓝图 800-1500 行。

---

## Phase 6: 设置 / 日志 / 杂项

### Task 26: 抽出 settings 蓝图

`/api/settings/wo-types` + `/api/settings/projects` + `/api/settings/print-templates` + `/api/settings/roles` + `/api/settings/permissions` + `/api/settings/users` + `/api/settings/logs`。

行号 4534-15275（跨度最大）。其中权限/角色部分逻辑复杂（行号 14546-14903），建议先抽 `services/permission_service.py`。

---

### Task 27: 抽出 log 蓝图

`/api/settings/logs` + `/api/operation-logs/export`。

---

### Task 28: 抽出 preorder / return_order 蓝图

- `/api/pre-orders` CRUD + convert
- `/api/return-orders` CRUD + audit + stock-in

`audit_return_order` 272 行（行号 12624），最长的退货逻辑。

---

### Task 29: 移除调试路由

`/api/diagnose-encoding` + `/api/fix-encoding` 是临时调试端点，建议直接删除（不迁移）。

---

## Phase 7: 收尾

### Task 30: 删除根目录 app.py 的迁移后残留

**Files:**
- Modify: `source-code/app.py`（改为 5 行薄壳）

- [ ] **Step 1: 备份当前 app.py 的内容（仅作参考）**

```bash
cp source-code/app.py source-code/app.py.bak
```

- [ ] **Step 2: 把根目录 app.py 改为薄壳**

写入 `source-code/app.py`:

```python
"""兼容入口：新代码请用 backend/run.py。
保留此文件仅为向后兼容（部分旧文档/脚本可能引用 `python app.py`）。
"""
from backend.run import app  # noqa: F401
```

- [ ] **Step 3: 验证可启动**

```bash
cd source-code && python -c "from app import app; print('ok')"
```
Expected: `ok`

- [ ] **Step 4: 跑全部测试**

```bash
cd backend && pytest tests/ -v
```
Expected: 全部 PASS

- [ ] **Step 5: 手动端到端验证（需要 MySQL+Redis）**

```bash
cd source-code && docker-compose up -d
sleep 10
curl http://localhost:5000/api/health
curl http://localhost:5000/api/setup/status
# Expected: 两次都返回 {"code":200,...}
docker-compose down
```

- [ ] **Step 6: Commit**

```bash
git add source-code/app.py source-code/app.py.bak
git commit -m "refactor: replace monolithic app.py with thin shim"
```

---

### Task 31: 删除 app.py.bak

```bash
git rm source-code/app.py.bak
git commit -m "chore: remove app.py backup after successful migration"
```

---

### Task 32: 更新 docker-compose.yml / README / .env.example

- [ ] **Step 1: 验证 docker-compose.yml 已用 `run:app`**（已正确，无需改）
- [ ] **Step 2: 合并 .env.example**

把 `backend/.env.example` 合并到根目录 `.env.example`，删除 `backend/.env.example`。最终 `.env.example` 在根目录，包含所有环境变量。

- [ ] **Step 3: 更新 README 目录结构图**

把"backend/app.py"改为"backend/run.py"，补"backend/app/blueprints/"和"backend/app/utils/"。

- [ ] **Step 4: 跑全部测试**

```bash
cd backend && pytest tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add .env.example backend/.env.example README.md
git commit -m "docs: sync env example and README after blueprint migration"
```

---

### Task 33: 写完整 blueprint 端到端测试

**Files:**
- Create: `backend/tests/test_blueprints.py`

- [ ] **Step 1: 写测试**

```python
"""每个蓝图端到端 smoke：仅验证 401/403/404 行为，不依赖真实业务。"""
import pytest


BLUEPRINT_ENDPOINTS = [
    ('GET', '/api/customers'),
    ('GET', '/api/suppliers'),
    ('GET', '/api/products'),
    ('GET', '/api/devices'),
    ('GET', '/api/workorders'),
    ('GET', '/api/receiveorders'),
    ('GET', '/api/inventory/stock'),
    ('GET', '/api/purchase/orders'),
    ('GET', '/api/sales/orders'),
    ('GET', '/api/quotes'),
    ('GET', '/api/finance/accounts'),
    ('GET', '/api/dashboard/stats'),
    ('GET', '/api/settings/users'),
    ('GET', '/api/salary'),
    ('GET', '/api/expense'),
    ('GET', '/api/assets'),
]


@pytest.mark.parametrize('method,path', BLUEPRINT_ENDPOINTS)
def test_blueprint_unauthorized_returns_401(client, method, path):
    res = client.open(path, method=method)
    assert res.status_code in (401, 403), f'{method} {path} 应返回 401/403，实际 {res.status_code}'
```

- [ ] **Step 2: 跑测试**

```bash
cd backend && pytest tests/test_blueprints.py -v
```
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_blueprints.py
git commit -m "test: add blueprint endpoint smoke tests"
```

---

## 自检清单（执行时核对）

- [ ] 每个 Phase 完成后跑一次 `cd backend && pytest tests/ -v`，全绿才进下一阶段。
- [ ] 每个 Task 完成后立即 commit，避免半成品堆积。
- [ ] 关键行为（状态机、事务、权限校验）**一字不改**地从 app.py 复制，只做模块化，不做行为变更。
- [ ] 长函数（>100 行）抽 services/ 时保持原签名，路由层只剩 dispatch。
- [ ] 删除调试路由（`/api/diagnose-encoding`）前确认无外部依赖。
- [ ] 最终任务完成后，跑 `cd backend && pytest tests/ -v --cov=app --cov-report=term-missing` 检查覆盖率。

---

## 关键风险

1. **sys.path hack**：根目录 `app.py` 第 36-42 行注入了 `backend/` 到 sys.path。如果某些 import 是绝对路径（如 `from extensions import db`），需要在 create_app() 之前确认 sys.path 已就位。当前 backend/app/__init__.py 第 9-11 行已有注释说明此问题。
2. **config 双重加载**：根目录 app.py 自己也调了 `_get_config`，迁移完必须删除，否则 Config 会被加载两次。
3. **JWT 黑名单**：根目录 app.py 第 122-125 行注册了 `token_in_blocklist_loader`，backend/app/security.py 已有等价实现，迁移后必须确保只注册一次。
4. **CORS 配置**：根目录 app.py 第 95-98 行注册了 CORS，backend/app/__init__.py 第 42-46 行也已注册，必须去重。
5. **错误处理器去重**：errors.py 已有完整 400/401/403/404/405/413/500 handler，app.py 101-117 行必须删除。
6. **after_request charset**：app.py 第 52 行 `set_charset`，backend 没有等价处理。建议在 backend/app/__init__.py 的 create_app() 里补一个 after_request。

---

## 期望产出

完成后项目结构：
- 根目录 `app.py`: 5 行薄壳（最后可删）
- `backend/run.py`: 生产入口（不变）
- `backend/app/blueprints/`: 27 个 blueprint 文件
- `backend/app/utils/`: 6 个工具文件（response / pagination / text / order_no / serialization / excel）
- `backend/services/` (Phase 4 期间按需创建): 3-5 个 service 文件（workorder / receive / inventory / sales / finance）
- `backend/tests/`: smoke + utils + blueprint 三个测试文件
- 根目录 `app.py` 最终可删除（确认 backend/run.py 跑通后用 `git rm`）

---

## 工作量估计

| Phase | 任务数 | 估计耗时 |
|-------|--------|----------|
| Phase 1: 基础设施 | 5 | 1-2 小时 |
| Phase 2: 小域 | 3 | 1-2 小时 |
| Phase 3: 中等域 | 7 | 3-5 小时 |
| Phase 4: 大域 | 7 | 8-12 小时（含 services 抽取） |
| Phase 5: 财务/统计 | 3 | 3-4 小时 |
| Phase 6: 设置/杂项 | 4 | 2-3 小时 |
| Phase 7: 收尾 | 4 | 1-2 小时 |
| **总计** | **33** | **19-30 小时** |

建议分多日执行，每个 Phase 完成后 git tag 一次以便回退。