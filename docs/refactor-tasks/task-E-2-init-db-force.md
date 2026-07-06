# Task E-2: init_db.py 加 --force 开关

## 目标
`python scripts/init_db.py` 默认拒绝覆盖已存在数据库；显式 `--force` 才允许重建。

## 涉及文件
`source-code/backend/scripts/init_db.py`

## 改法

### 在 `init_database()` 函数顶端加 argparse
位置：找到 `def init_database():` 那行后立刻插入。

```python
def init_database():
    """执行 init.sql + 写入种子数据。"""
    import argparse
    parser = argparse.ArgumentParser(description='初始化 SQLite 数据库')
    parser.add_argument(
        '--force', action='store_true',
        help='已存在数据库时也覆盖（危险：会清空所有业务数据）',
    )
    args, _ = parser.parse_known_args()
```

### 修改 unlink 逻辑
找到这段（第 277-291 行附近）：
```python
if db_file.exists():
    print(f'[init_db] 警告：{db_file} 已存在，将被覆盖')
    db_file.unlink()
```

改为：
```python
if db_file.exists():
    if not args.force:
        raise RuntimeError(
            f'数据库已存在：{db_file}\n'
            f'如确认要重建，请加 --force 参数（会清空全部业务数据）。'
        )
    print(f'[init_db] --force：覆盖 {db_file}')
    db_file.unlink()
```

`if __name__ == '__main__': init_database()` 保持不变（argparse 会自动从 `sys.argv` 读）。

## 不要碰
- 不要改 `init.sql`
- 不要改 `_seed()` 函数
- 不要改 `migrate_status` 调用

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe scripts/init_db.py
# 期望抛 RuntimeError "数据库已存在..."
.venv/Scripts/python.exe scripts/init_db.py --force
# 应正常重建（如要保留业务数据，本次不应跑 --force）
```

注意：**执行 `init_db.py --force` 会清空业务数据**。仅在没有业务数据的库上跑，或者已经手工备份过的库。

## 提交
```
feat(init-db): 加 --force 开关防止误删

- 默认拒绝覆盖已有 db
- --force 才允许重建
```

## 回滚
```bash
git checkout source-code/backend/scripts/init_db.py
```
