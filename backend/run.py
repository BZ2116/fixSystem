"""
应用入口
- 开发环境：`python run.py`
- 生产环境：`gunicorn run:app`
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env（无论 cwd 在哪）。生产环境通过 docker-compose 注入。
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / '.env')

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'production'))


@app.shell_context_processor
def make_shell_context():
    from extensions import db
    return {'db': db}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))