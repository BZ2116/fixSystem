# Task A-0: dispatch.py 三行 AttributeError 修复

## 目标
派单管理页（`GET /api/dispatch/pending`）当前 500。消除这个 500。

## 涉及文件
- `source-code/backend/app/blueprints/dispatch.py:410, 411, 422`

## 改法
3 处 `reception_user_id` → `receiver_id`，第 422 行 `reception_user_name` → `receiver_name`。

```python
# 原（410 行附近）
if o.reception_user_id:                  # 410
    user_ids.add(o.reception_user_id)    # 411
...
d['reception_user_name'] = users_map.get(o.reception_user_id, '')  # 422

# 改为
if o.receiver_id:
    user_ids.add(o.receiver_id)
...
d['receiver_name'] = users_map.get(o.receiver_id, '')
```

字段名已与 `work_order` 表 / `WorkOrder` 模型一致（`receiver_id`），不是新增字段。

## 不要碰
任何其他文件。

## 验证
```bash
cd source-code/backend
.venv/Scripts/python.exe -m pytest tests/test_blueprints.py -k dispatch -x
```
或：浏览器进「派单管理」，应返回列表不再 500。

```bash
grep -c "reception_user_id" source-code/data/logs/flask.log
# 应 = 0（或只剩历史）
```

## 提交
```
fix(dispatch): 修 WorkOrder.reception_user_id 误用

- dispatch.py:410/411/422 改为 receiver_id / receiver_name
- 与 work_order.assigned_user_id 之外的 receiver_id 字段对齐
```

## 回滚
```bash
git checkout source-code/backend/app/blueprints/dispatch.py
```
