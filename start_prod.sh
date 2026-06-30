#!/usr/bin/env bash
# ============================================================
# Repair System - 生产模式启动 (Linux/macOS): gunicorn
# ============================================================
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then cp .env.example .env; fi
if [ ! -d backend/.venv ]; then
    cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && cd ..
fi
if [ ! -f data/repair_system.db ]; then
    cd backend && source .venv/bin/activate && python scripts/init_db.py && cd ..
fi
if [ ! -f frontend/dist/index.html ]; then
    cd frontend && npm install && npm run build && cd ..
fi

echo "[start_prod] 启动 gunicorn ..."
cd backend
source .venv/bin/activate
FLASK_ENV=production exec gunicorn -w 2 -b 0.0.0.0:5000 run:app