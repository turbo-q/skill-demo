# 漏洞扫描 Agent 示例

本示例演示：

- **Middleware 架构**：使用 `deepagents.create_deep_agent`，显式配置 **Skills** 中间件
- **Skills**：由官方 `deepagents.middleware.skills.SkillsMiddleware` 自动管理（从 `app/skills/` 加载 SKILL.md），无需手动检索。
- **Tools**：核心工具在 `app/tools/` 目录（端口扫描、HTTP 探测），由 `build_vuln_scan_tools()` 统一注册。
- **Checkpoint**：LangGraph `MemorySaver` 持久化对话状态（thread_id = session_id），支持多轮与恢复。
- **Storage**：StorageManager + ContextManager + SQLite Backend，会话与历史持久化到数据库。
- **完整 UI**：`frontend/` 下独立静态页，侧栏会话列表 + 主区聊天，Tailwind 样式。

## 环境准备（uv）

```bash
uv sync
# 非OPENAI也可以在页面进行配置
export OPENAI_API_KEY="your-key"
```

（未安装 uv 时：`pip install uv` 或见 [uv 文档](https://docs.astral.sh/uv/)）

## 启动对话 UI

`uv run python run_web.py`、`uv run uvicorn app.web:app --reload --host 0.0.0.0 --port 8000`

浏览器打开 http://localhost:8000 ，使用完整 UI：侧栏选择/新建会话、输入用户 ID、发送消息；新会话自动创建，点击会话可加载历史。

## 技能测试流程

### 1. 确认技能已存在

当前示例技能（均由 SkillsMiddleware 自动加载）：

| 技能目录               | 用途                         | 触发示例 |
|------------------------|------------------------------|----------|
| `app/skills/ping-check/`    | 连通性检查                   | 「帮我检查 127.0.0.1 是否通」「ping 一下 example.com」 |
| `app/skills/scan-report/`  | **工具外部脚本调用示例**：通过 execute 执行技能内脚本，输出报告模板 | 「生成一份漏洞扫描报告模板」「给我扫描报告格式」 |


### 3. 在页面配置模型

- 打开 http://localhost:8000
- 侧栏「模型配置」：填写 **Base URL**、**API Key**（或依赖环境变量）
- 点击 **获取模型列表**，选择模型后点击 **保存配置**

### 4. 发消息触发技能

- 新会话或选已有会话，在输入框发送与技能相关的自然语言，例如：
  - 测 **ping-check**：`帮我检查 127.0.0.1 的 80 端口是否通`
  - 测 **scan-report**（工具外部脚本示例）：`生成一份漏洞扫描报告模板`
- Agent 会按上下文注入对应技能说明，并调用绑定工具（如 `tcp_port_scan`、`http_get`、`execute`）执行；scan-report 会通过 execute 运行 `app/skills/scan-report/scripts/generate_template.py` 输出模板。

### 5. 如何确认技能生效

- 回复中应包含与技能一致的步骤或结论（如端口开放情况、扫描建议）。
- 若开启调试日志，可看到 SkillsMiddleware 注入的技能名称或片段。

### 查看「用了哪个技能 / 提示词」：日志

- **默认（INFO）**：每次 LLM 调用会打「消息数 + 前几条摘要」；每次工具调用会打「工具名 + 入参/结果摘要」。
- **完整 prompt（含技能注入）**：先设置环境变量再启动：
  ```bash
  LOG_LEVEL=DEBUG uv run python run_web.py
  ```
  控制台会输出本次发给模型的完整 messages（system、历史、当前轮），便于确认 SkillsMiddleware 注入了哪些技能内容。

deepagents 官方更推荐用 [LangSmith](https://smith.langchain.com/) 做完整追踪；本地用上述 callback 即可看提示词与工具。

### 7. 新增自定义技能

1. 在 `app/skills/` 下新建文件夹，如 `my-skill/`。
2. 新建 `SKILL.md`，front-matter 中 **name** 必须为小写英文+连字符（如 `name: my-skill`），否则会报规范提示。
3. 填写 `description`、`tags`、`tools`（可选 `script`），保存后重启或等中间件重新加载即可被检索注入。

## 项目结构摘要

- `app/skills/`：Skill 目录（每技能一个文件夹 + SKILL.md + 可选 scripts/），由 `deepagents.middleware.skills.SkillsMiddleware` 自动加载。
- `app/tools/`：核心工具目录（`port_scan.py`、`http_get.py`），`build_vuln_scan_tools()` 供 Agent 挂载。
- `app/agent_vuln.py`：Agent 构造函数（`get_agent()`），使用 `create_deep_agent` + Skills 中间件 + LangGraph checkpoint。
- `app/run.py`：主流程，封装 session 管理 + 历史加载 + agent 调用 + 消息存储。
- `app/storage/`：StorageManager + ContextManager + SQLite Backend，会话与消息持久化。
- `app/web.py`：FastAPI 对话 API（`/api/chat`、`/api/sessions`、`/api/history`），根路径挂载 `frontend/`。
- `frontend/index.html`：完整对话 UI（侧栏 + 会话列表 + 消息区 + 输入）。
