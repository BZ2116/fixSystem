# Agent 任务上下文（每次分发必读）

> 给所有 agent 的统一背景。每个任务 md 已自包含，单张即可执行；本文件是惯例与红线补充。

## 项目一句话
维修商贸一体化管理系统。Vue 3 + Flask + SQLite 单文件部署，单店 ≤5 并发用户。

## 关键路径
- 后端代码：`source-code/backend/`
- 前端代码：`source-code/frontend/`
- 数据：`source-code/data/repair_system.db`
- 运行时配置：`source-code/.env`（项目根）
- 后端示例配置：`source-code/backend/.env.example`
- 主整改方案：`source-code/REFACTOR_PLAN.md`

## 工作约定
1. **结论先行**：每条回复先把结果说清楚，再给理由。
2. **必做验证**：每个任务完成后跑"验证步骤"列的命令，失败就别交付。
3. **别绕**：如果测试失败，找根因，不要改测试、加 `pass # noqa`、注释掉报错代码。
4. **不要改任务 md 之外的代码**：每个任务卡明确"禁止触碰"，没列到的文件就别动。
5. **别引入新依赖**：除非任务 md 明示，否则不碰 `requirements.txt` / `package.json`。

## 验证标准
- 后端：`cd source-code/backend && .venv/Scripts/python.exe -m pytest tests/ -v`
- 前端：`cd source-code/frontend && npm run build`
- 数据库完整：`python -c "import sqlite3; sqlite3.connect('../data/repair_system.db').execute('SELECT 1').fetchone()"`

## 提交格式
```
<type>(<scope>): <subject>

<body: 简述为什么>
```

- type ∈ fix / feat / refactor / test / docs / chore
- scope = 触及的模块名（如 dispatch、customer、init-db）
- subject ≤ 60 字，不用句号

## 完成后回报（给主控时附上）
- 触达文件清单（含行号）
- pytest / npm 输出最后一行的 pass / fail
- 浏览器截图（仅 UI 改动）
- 任何未完成项

## 红线（任何 agent 都不要做）
- 不 `git push`
- 不 `git commit --amend` 别人的提交
- 不 hard reset
- 不改 SQLite db 文件
- 不改 `source-code/.env` 之外的环境（除非任务明示）
- 不在 .py 里加 `print()` 调试后留下
