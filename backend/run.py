"""
应用入口
- 开发环境：`python run.py`
- 生产环境：`gunicorn run:app`
"""
import os
from dotenv import load_dotenv

# 加载 .env（仅开发环境；生产环境通过 docker-compose 注入）
if os.path.exists('.env'):
    load_dotenv()

from app import create_app

app = create_app(os.environ.get('FLASK_ENV', 'production'))


@app.shell_context_processor
def make_shell_context():
    from extensions import db
    return {'db': db}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', False))