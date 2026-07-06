# Repair System Portable Tech Stack & Data Storage Design

**Date**: 2026-06-30
**Status**: Draft (pending user review)
**Scope**: Lock the tech stack and data storage decisions for the SQLite-portable variant of the repair-system, plus the migration approach from the current MySQL/Redis/docker-compose stack.

---

## 1. Goal & Constraints

**Primary goal**: Package the entire repair-system into a portable zip that can be unzipped on another computer and started with minimal installation. Data lives in local files alongside the code.

**Constraints**:
- Single-machine / small-team use (≤ 5 concurrent users)
- Cross-platform (Windows primary, Linux/Mac secondary)
- Zero docker / zero external services at runtime
- Default admin credentials and config preserved (one-click startup)
- Current feature set (27+ blueprints, workorder/receiveorder/inventory/finance/etc.) must continue to work

**Non-goals**:
- Horizontal scaling / multi-server deployment
- High-concurrency writes (SQLite is the limit)
- Cloud-native deployment (no S3, no managed DB)

---

## 2. Architecture Overview

### Runtime architecture (single process, file-based storage)

```
Browser (Chrome/Edge)
        │ HTTP
        ▼
  ┌─────────────┐
  │  Frontend   │  Vite dev server :5173 (dev) / static files (prod)
  │ Vue 3 +     │  axios + JWT (Authorization: Bearer)
  │ Element Plus│
  └─────┬───────┘
        │ /api/* JSON
        ▼
  ┌─────────────┐
  │ Flask       │  run.py :5000  (gunicorn prod / flask run dev)
  │ blueprints/ │  JWT auth + permission decorators
  │ services/   │
  └─┬───────┬───┘
    │       │
    ▼       ▼
  data/   data/
  SQLite  uploads/
  (.db)   (local dir)
```

### Directory layout (final state)

```
repair-system/                       # project root (= portable zip contents)
├── backend/
│   ├── run.py                       # production entry
│   ├── app/                         # factory + blueprints + services + utils
│   ├── models/                      # SQLAlchemy models (per domain)
│   ├── database/init.sql            # SQLite schema + seed data
│   ├── scripts/
│   │   ├── init_db.py               # read init.sql + execute + seed
│   │   └── start_dev.py             # launch Flask + Vite with PID files
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_smoke.py
│   │   ├── test_utils.py
│   │   └── test_blueprints.py
│   └── requirements.txt
├── frontend/
│   ├── src/                         # views / router / stores / api / styles
│   ├── dist/                        # pre-built (production)
│   ├── package.json
│   └── vite.config.js
├── data/                            # ★ data dir (migrates with the project)
│   ├── repair_system.db             # SQLite (business + JWT blacklist)
│   ├── repair_system.db-wal
│   ├── repair_system.db-shm
│   ├── uploads/                     # user-uploaded files
│   ├── logs/                        # flask.log + vite.log
│   └── .pids/                       # flask.pid + vite.pid
├── docs/
│   ├── superpowers/specs/
│   ├── superpowers/plans/
│   └── archive/docker-configs/      # deprecated docker files (transitional)
├── start.bat                        # Windows dev-mode entry
├── start.sh                         # Linux/Mac dev-mode entry
├── start_prod.bat                   # Windows production-mode entry
├── start_prod.sh                    # Linux/Mac production-mode entry
├── stop.bat / stop.sh               # stop all services via PID files
├── .env.example
├── .gitignore
├── README.md
└── VERSION.txt
```

### Migration from current state

| Current | Final | Action |
|---------|-------|--------|
| `docker-compose.yml` | — | Move to `docs/archive/docker-configs/`, then delete after 2 weeks |
| `backend/Dockerfile` | — | Same |
| `frontend/Dockerfile` | — | Same |
| `frontend/nginx.conf` | — | Same |
| `.dockerignore` (if exists) | — | Same |
| `database_complete_v3.sql` (60k lines, MySQL) | `docs/archive/database_complete_v3.sql` | Reference only; not used at runtime |
| New | `backend/database/init.sql` | SQLite version, written from scratch |
| `backend/.env.example` | Merged into root `.env.example` | Single env file |
| `app.py` (root, shim) | **Deleted** | `backend/run.py` is the only entry |
| New | `backend/scripts/init_db.py` | Reads init.sql + executes + seeds |
| New | `backend/scripts/start_dev.py` | Manages Flask + Vite via PID files |
| New | `data/.pids/`, `data/logs/`, `data/uploads/` | Created on first run |
| New | `start.bat / start.sh / stop.bat / stop.sh` | Cross-platform entry scripts |

---

## 3. Tech Stack (Final)

### Frontend (unchanged)

| Component | Version | Role |
|-----------|---------|------|
| Vue | 3.2.47 | SPA |
| Vite | 4.4.9 | Dev server / build |
| Element Plus | 2.2.28 | UI components |
| Vue Router | 4.1.6 | Routing |
| Pinia | 2.0.36 | State management |
| Axios | 1.5.0 | HTTP client (with JWT interceptor) |
| ECharts | 5.4.3 | Charts |
| jsbarcode, qrcode, xlsx, dayjs, lodash-es, pinyin | — | Utilities |

### Backend

| Component | Version | Role |
|-----------|---------|------|
| Python | 3.11+ | Runtime |
| Flask | 2.3.3 | Web framework |
| Flask-SQLAlchemy | 3.0.5 | ORM (`sqlite://` URL) |
| Flask-JWT-Extended | 4.5.2 | JWT auth (blacklist now in SQLite) |
| Flask-Migrate | 4.0.5 | Migrations (kept for future) |
| Flask-CORS | 4.0.0 | CORS |
| Flask-Talisman | 1.1.0 | Security headers (disabled in dev) |
| bcrypt | 4.1.2 | Password hashing |
| gunicorn | 21.2.0 | Production WSGI |
| openpyxl | 3.1.2 | Excel I/O |
| pypinyin | 0.51.0 | Pinyin initials (product/customer codes) |
| ~~PyMySQL~~ | — | **Removed** (SQLite uses Python's built-in sqlite3) |
| ~~redis~~ | — | **Removed** |

### Data storage

| Component | Source | Role |
|-----------|--------|------|
| SQLite | Python stdlib (`sqlite3`) | Primary DB + JWT blacklist |
| Local filesystem | OS | Uploaded files (`data/uploads/`) |

### External dependencies on target machine

- Python 3.11+ (only required install on target machine)
- Node.js (only needed in **dev mode**; production ships pre-built `frontend/dist/`)

**Not required on target machine**: MySQL, Redis, Docker, Node (production).

---

## 4. SQLite Adaptation

### Configuration

`backend/app/config.py`:
```python
SQLALCHEMY_DATABASE_URI = f'sqlite:///{ROOT}/data/repair_system.db'
SQLALCHEMY_ENGINE_OPTIONS = {
    'connect_args': {
        'timeout': 5,        # busy_timeout in seconds
        'check_same_thread': False,
    }
}
```

Per-connection PRAGMA (set in `extensions.py` via event listener):
```sql
PRAGMA journal_mode = WAL;        -- read/write concurrency
PRAGMA synchronous = NORMAL;       -- small reliability trade-off for speed
PRAGMA foreign_keys = ON;          -- enable FK constraints
PRAGMA busy_timeout = 5000;        -- 5s wait for write lock
```

### MySQL → SQLite translation rules

| MySQL feature | Count in current schema | SQLite replacement |
|--------------|------------------------|---------------------|
| `ENUM` | 0 | N/A |
| `ON UPDATE CURRENT_TIMESTAMP` | 18 | **App-layer**: `before_update` hook in each model sets `updated_at = datetime.now()` |
| `JSON` | 2 | SQLAlchemy `db.JSON` (cross-dialect); app uses `json.loads/dumps` |
| `TEXT/VARCHAR/CHAR` | 187 | Native SQLite support, no change |
| Stored procedures (`safe_add_*`) | 3 | Drop entirely — SQLite doesn't need idempotent ALTER |
| `BIGINT AUTO_INCREMENT` | all PKs | `db.Integer` (SQLAlchemy translates) |
| `MATCH AGAINST` (full-text) | 0 currently | Keep `LIKE '%xxx%'` for now |

### App-layer timestamp pattern

```python
# backend/models/_base.py
from datetime import datetime
from extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
```

Note: SQLAlchemy's `onupdate` runs in the app layer, so this works for SQLite.

### JWT blacklist (replaces Redis)

```sql
CREATE TABLE jwt_blacklist (
    jti VARCHAR(64) PRIMARY KEY,
    revoked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL
);
CREATE INDEX idx_jwt_blacklist_expires_at ON jwt_blacklist(expires_at);
```

`backend/app/security.py` changes:
```python
from flask_jwt_extended import get_jwt
from extensions import db
from datetime import datetime


@jwt.token_in_blocklist_loader
def check_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    expires_at = datetime.fromtimestamp(jwt_payload['exp'])
    row = db.session.execute(
        db.text('SELECT 1 FROM jwt_blacklist WHERE jti = :jti AND expires_at > :now'),
        {'jti': jti, 'now': datetime.now()}
    ).first()
    return row is not None


def revoke_token(jwt_payload):
    """Called on logout."""
    jti = jwt_payload['jti']
    expires_at = datetime.fromtimestamp(jwt_payload['exp'])
    db.session.execute(
        db.text('INSERT OR IGNORE INTO jwt_blacklist (jti, expires_at) VALUES (:jti, :exp)'),
        {'jti': jti, 'exp': expires_at}
    )
    db.session.commit()


def cleanup_expired_blacklist():
    """Run on startup and daily."""
    db.session.execute(
        db.text('DELETE FROM jwt_blacklist WHERE expires_at < :now'),
        {'now': datetime.now()}
    )
    db.session.commit()
```

### Concurrency limits (documented in README)

- SQLite serializes writes; concurrent writes will block
- Reads are concurrent (WAL mode)
- **Documented limit**: ≤ 5 concurrent users, suitable for single-shop / small-team use

---

## 5. Data Storage

### SQLite database

- **File**: `data/repair_system.db`
- **Tables** (approx 50+): all business tables from current MySQL schema + new `jwt_blacklist`
- **Indexes**: all FKs + business search fields (`name`, `code`, `phone`, `created_at`) + composite indexes for hot queries

### File uploads

- **Directory**: `data/uploads/`
- **Structure**:
  ```
  data/uploads/
  ├── avatar/         # user avatars
  ├── workorder/      # workorder photos
  ├── receive/        # receive-order photos
  ├── product/        # product images
  ├── customer/       # customer docs
  ├── temp/           # temporary (Excel imports)
  └── print/          # generated PDFs/Excels
  ```
- **Limit**: `MAX_CONTENT_LENGTH_MB = 16` (unchanged)

### Backup strategy

| Scenario | Method |
|----------|--------|
| Routine | Stop services → copy `data/repair_system.db` + `.db-wal` + `.db-shm` → restart |
| Project migration | Stop services → zip whole `repair-system/` excluding `__pycache__`, `.venv`, `node_modules` |
| Disaster recovery | Delete `data/repair_system.db` → rerun `init.sql` → data lost but schema intact |

**Standard backup procedure** (documented):
1. Run `stop.bat` / `stop.sh`
2. Copy `data/repair_system.db*` to backup location
3. Restart with `start.bat` / `start.sh`

---

## 6. Startup Flow

### Entry scripts

| Script | Platform | Role |
|--------|----------|------|
| `start.bat` / `start.sh` | Windows / Linux-Mac | **Dev mode**: Flask + Vite |
| `start_prod.bat` / `start_prod.sh` | Windows / Linux-Mac | Production: gunicorn + static |
| `stop.bat` / `stop.sh` | Windows / Linux-Mac | Stop all via PID files |

### `start.bat` logic (dev mode)

```
1. python --version  (fail with message if missing)
2. If .env missing → copy .env.example .env
3. If backend\.venv missing → python -m venv + pip install
4. If data\repair_system.db missing → python scripts\init_db.py
5. If frontend\node_modules missing → npm install
6. python scripts\start_dev.py  (manages Flask + Vite via PIDs)
```

### `scripts/start_dev.py` (cross-platform process manager)

- Starts Flask (port 5000) and Vite (port 5173)
- Writes PID files to `data/.pids/flask.pid` and `vite.pid`
- Redirects stdout/stderr to `data/logs/flask.log` and `vite.log`
- Monitors both processes; exits if either dies
- On Ctrl+C / SIGTERM: cleans up both processes and removes PID files

### `scripts/init_db.py`

1. Create `data/` if missing
2. Connect to `data/repair_system.db`
3. Execute `backend/database/init.sql` (full schema in one script)
4. Insert seed data:
   - Default admin (`admin` / `123456`, bcrypt-hashed)
   - Default roles (admin / technician / finance / warehouse)
5. Commit and close

### First-run vs subsequent-run behavior

| Check | First run | Subsequent |
|-------|-----------|------------|
| `.env` | Copy from example | Skip |
| `backend/.venv/` | Create + pip install | Activate existing |
| `data/repair_system.db` | Run init.sql + seed | Skip |
| `frontend/node_modules/` | npm install | Skip |
| Flask + Vite | Start | Start |

---

## 7. Cross-Computer Migration

```
Source machine                        Target machine
─────────────                        ─────────────
1. Run stop.bat                      3. Unzip to any directory
2. Run scripts/build_portable.bat       (or extract via 7z)
   → produces repair-system-         4. Install Python 3.11+ (if missing)
     portable-v{VERSION}.zip          5. Double-click start.bat
                                       → auto-creates venv
                                       → pip install
                                       → detects existing data/ → skips init
                                       → starts Flask + Vite
                                     6. Open http://localhost:5173
```

### `scripts/build_portable.bat` (lives on dev machine, not in zip)

```batch
@echo off
REM Clean transient files
for /d /r backend %%d in (__pycache__) do @rd /s /q "%%d" 2>nul
for /d /r frontend %%d in (node_modules) do @rd /s /q "%%d" 2>nul
if exist backend\.venv rd /s /q backend\.venv

REM Build frontend for production
cd frontend
call npm install
call npm run build
cd ..

REM Zip (excluding transient dirs)
powershell -Command "Compress-Archive -Path backend,frontend,data,docs,start.bat,start.sh,start_prod.bat,start_prod.sh,stop.bat,stop.sh,.env.example,.gitignore,README.md,VERSION.txt -DestinationPath repair-system-portable-v%1.zip -Force"
echo [OK] Built repair-system-portable-v%1.zip
```

---

## 8. Error Handling

### Flask layer
- Keep current `register_error_handlers` (400/401/403/404/405/413/500)
- Unchanged from current implementation

### SQLite-specific errors

| Scenario | Error | Handling |
|----------|-------|----------|
| DB locked | `OperationalError: database is locked` | Auto-retry 3x with 0.5s delay via `retry_on_lock` decorator |
| Disk full | `OperationalError: database or disk is full` | Return 500 with user-friendly message |
| DB corrupted | `DatabaseError: database disk image is malformed` | Return 500, log details, suggest restore from backup |
| FK violation | `IntegrityError: FOREIGN KEY constraint failed` | Catch in service layer, return 400 with field-level error |

### Retry decorator

`backend/app/utils/db_retry.py`:
```python
import time, functools
from sqlite3 import OperationalError


def retry_on_lock(max_retries=3, delay=0.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if 'locked' not in str(e) or i == max_retries - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator
```

Apply to: workorder create, inventory changes, finance writes.

### Logging

- **Flask**: `data/logs/flask.log` (stdout/stderr redirect)
- **Vite**: `data/logs/vite.log`
- **Operation log**: kept in DB (`operation_log` table), behavior unchanged
- **Slow query log**: SQLite doesn't support; not needed at this scale

---

## 9. Testing Strategy

### Layers

| Layer | Tool | DB | Speed |
|-------|------|----|------|
| Unit | pytest | in-memory SQLite | < 1s |
| Integration | pytest + Flask test client | in-memory SQLite | few sec |
| End-to-end | pytest + Flask test client | temp file SQLite | few sec |

### Fixtures (`backend/tests/conftest.py`)

```python
import pytest
from app import create_app
from extensions import db


@pytest.fixture
def app():
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
```

### Test command

```bash
cd backend && pytest tests/ -v
```

### Existing test files (preserved)

- `tests/test_smoke.py` — health + auth + blueprint 401/403
- `tests/test_utils.py` — response/pagination/order_no
- `tests/test_blueprints.py` — 27 blueprints end-to-end

### Migration-specific test changes

- `conftest.py`: URI switches to `sqlite:///:memory:`
- Remove MySQL-specific dialect checks
- JSON field assertions use Python lists (after `json.loads`)
- `updated_at` assertions rely on app-layer behavior (not DB)

---

## 10. Open Items / Future Work

These are explicitly **not** in scope for this spec; document them in README for future consideration:

| Item | Trigger | Potential solution |
|------|---------|-------------------|
| Object storage for uploads | `data/uploads/` > 10 GB | Migrate to MinIO / S3 |
| Full-text search | `LIKE '%xxx%'` becomes slow | SQLite FTS5 extension |
| Message queue / async tasks | Large Excel exports block UI | Background thread / Celery |
| Centralized logging | Logs scattered in `data/logs/` | Ship to Loki / ELK |
| Metrics / monitoring | Need latency / error visibility | Prometheus client + dashboard |
| Multiple concurrent writers | > 5 simultaneous writers | Migrate back to PostgreSQL/MySQL |
| HTTPS | Network deployment | Reverse proxy (Caddy / Nginx) |
| Mobile app | Customer-facing scenarios | PWA / separate mobile |

---

## 11. Decisions Locked (user-confirmed)

1. **Goal**: Confirm current stack + close gaps (not full re-evaluation)
2. **Local execution**: Native install (no docker)
3. **Database**: SQLite (replaces MySQL), with `data/` directory
4. **Cache/session**: Removed (Redis replaced by SQLite `jwt_blacklist` table)
5. **File storage**: Local directory (no object storage)
6. **Packaging**: Portable zip + Python script (PyInstaller not used)
7. **DB initialization**: Manual script run on first launch
8. **Docker files**: Move to `docs/archive/docker-configs/` first, delete after 2 weeks
9. **Database schema**: New SQLite `init.sql` written from scratch (NOT a slimmed MySQL version)
10. **`ON UPDATE CURRENT_TIMESTAMP`**: App-layer handling (18 places)
11. **`ENUM`**: 0 places, no action needed
12. **`JSON`**: 2 places, handled via SQLAlchemy `db.JSON` (cross-dialect)
13. **`init_db.py`**: Reads init.sql + executes + inserts seed data
14. **Process management**: PID files (not window-title matching)
15. **Default startup mode**: Dev mode (Flask + Vite)
16. **`.env`**: Defaults from `.env.example` (admin/123456, default JWT_SECRET)
17. **Schema reference**: Keep `database_complete_v3.sql` in `docs/archive/` for reference
18. **`data/logs/` and `backend/scripts/`**: Added to directory structure