# Task A-1: JWT 密钥升级到 ≥32 字节

## 目标
消除每次请求的 `InsecureKeyLengthWarning`。

## 涉及文件
- `source-code/.env`（运行时）
- `source-code/.env.example`（已 commit 的根示例）

## 改法

### 1. 生成密钥
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
将输出复制。

### 2. 写到 `.env`
把根目录 `.env` 中第 8 行 `JWT_SECRET_KEY=` 后面的值替换：
```
JWT_SECRET_KEY=<刚生成的 64 字节随机串>
```

### 3. `.env.example` 改成占位
```
JWT_SECRET_KEY=__SET_ME_TO_RANDOM_64_BYTES__before_first_run__
```

## 不要碰
- 不要把密钥写到 `.env.example`（绝对不能 commit 出去）
- 不要改 `backend/.env.example`（这是另一个文件，Task E-1 才动）
- 不要影响其他 secret

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -c "from app import create_app; create_app('development'); print('ok')"
grep -c "InsecureKeyLengthWarning" data/logs/flask.log
# 应 = 0
curl http://localhost:5000/api/health
# 期望 {"status":"healthy","db":true}
```

注意：密钥改了**所有已签发的 token 失效一次**，属正常。

## 提交
```
chore(security): JWT 密钥升级到 ≥32 字节随机串

- 消除 InsecureKeyLengthWarning
- .env.example 改为占位占位符
```

`.env` 文件**不要 commit**（`.gitignore` 应该已经排除，但要确认）。

## 回滚
```bash
git checkout source-code/.env.example
# .env 手动改回
```
