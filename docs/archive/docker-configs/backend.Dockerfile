FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 系统依赖（gcc 用于编译 cryptography/pymysql 等，tzdata 用于时区）
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        default-libmysqlclient-dev \
        pkg-config \
        tzdata \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# 上传目录
RUN mkdir -p /app/uploads

# 非 root 运行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:5000/api/health || exit 1

CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "4", \
     "-b", "0.0.0.0:5000", "--timeout", "120", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "run:app"]