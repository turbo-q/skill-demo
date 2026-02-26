# 架构说明

本项目使用 `deepagents.create_deep_agent` 构建漏洞扫描 Agent。

## 核心架构

### 1. Agent 构造（deepagents.create_deep_agent）

使用 **`deepagents.create_deep_agent`**，同时支持 **middleware + checkpoint**：

```python
from app.agent_vuln import get_agent

# 构建 agent（自动包含 middleware + checkpoint）
agent = get_agent()
```

**特点**：
- ✅ **Middleware 链**：TodoList（默认） + Skills（自定义） + Summarization（默认）
- ✅ **Checkpoint**：InMemorySaver（thread_id = session_id），支持多轮对话状态恢复
- ✅ **Skills 自动注入**：由 `SkillsMiddleware` 从 `app/skills/` 加载 SKILL.md

### 2. Skills 管理（自动注入）

**由 `deepagents.middleware.skills.SkillsMiddleware` 自动管理**：

```python
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.backends.filesystem import FilesystemBackend

skills_dir = Path(__file__).resolve().parent / "skills"
backend = FilesystemBackend(root_dir=str(skills_dir))
skills_middleware = SkillsMiddleware(backend=backend, sources=["."])
```

**技能目录结构**：
```
app/skills/
  web_basic_scan/
    SKILL.md           # 技能定义（YAML front-matter + Markdown 说明）
    scripts/
      checklist.py     # 可选：可执行脚本
```

**SKILL.md 格式**：
```yaml
---
id: web_basic_scan
name: 基础 Web 漏洞扫描流程
description: 适用于对单个 Web 站点进行初步安全扫描
tags: [web, vuln, scan]
tools: [tcp_port_scan, http_get]
script: scripts/checklist.py  # 可选
---

详细的技能说明...
```

**自动注入逻辑**：
- SkillsMiddleware 根据对话上下文智能推荐相关技能
- 技能说明自动注入到 agent 的 prompt 中
- 无需手动检索或调用

### 3. Checkpoint 持久化

使用 LangGraph checkpoint（`InMemorySaver`）：

```python
config = {"configurable": {"thread_id": session_id}}
result = await agent.ainvoke({"messages": messages}, config=config)
```

**特点**：
- `thread_id` = `session_id`，支持多轮对话与状态恢复
- 可扩展为 `SqliteSaver`、`PostgresSaver` 等

### 4. Storage 持久化

使用 `StorageManager` + `ContextManager` + `SQLiteBackend` 持久化会话与消息：

```python
from app.storage import get_storage_manager

storage = get_storage_manager()

# 创建/获取会话
ctx = await storage.context.get_or_create_session(
    session_id=session_id,
    user_id=user_id,
)

# 添加消息
await storage.context.add_message(session_id, "user", user_message)
await storage.context.add_message(session_id, "assistant", assistant_reply)

# 获取历史
history = await storage.context.get_conversation_history(session_id, limit=50)
```

### 5. 主流程

`app/run.py` 封装完整的对话流程：

```python
from app.run import run

session_id, reply = await run(
    user_message="扫描 example.com",
    metadata={"session_id": "xxx", "user_id": "alice"},
)
```

**流程**：
1. 初始化 storage（数据库）
2. 获取/创建会话
3. 添加用户消息
4. 构建 agent（checkpoint 自动恢复状态）
5. 加载历史消息
6. 调用 agent（Skills 自动注入）
7. 添加 assistant 回复
8. 返回 `(session_id, reply)`

### 6. 工具系统

核心工具在 `app/tools/` 目录：

```python
from app.tools import build_vuln_scan_tools

tools = build_vuln_scan_tools()
# 返回: [PortScanTool(), HttpGetTool()]
```

**工具列表**：
- `tcp_port_scan`: TCP 端口扫描
- `http_get`: HTTP 探测

## Middleware 链

`create_deep_agent` 的完整 middleware 链：

1. **TodoListMiddleware**（默认）：自动管理任务列表
2. **SkillsMiddleware**（自定义）：自动注入技能知识
3. **SummarizationMiddleware**（默认）：自动摘要长对话

其他默认 middleware：
- FilesystemMiddleware
- SubAgentMiddleware
- AnthropicPromptCachingMiddleware
- PatchToolCallsMiddleware

## 项目结构

```
app/
  agent_vuln.py          # Agent 构造（get_agent + create_deep_agent）
  run.py                 # 主流程
  web.py                 # FastAPI 对话 API
  db.py                  # 数据库初始化
  models.py              # SQLAlchemy 模型
  config.py              # 配置
  tools/                 # 核心工具
    __init__.py          # build_vuln_scan_tools()
    port_scan.py         # PortScanTool
    http_get.py          # HttpGetTool
  storage/               # 存储层
    __init__.py          # get_storage_manager()
    storage_manage.py    # StorageManager
    context_manager.py   # ContextManager
    backend.py           # SQLiteBackend
  skills/                # 技能目录（由 SkillsMiddleware 自动加载）
    README.md
    web_basic_scan/
      SKILL.md
      scripts/
        checklist.py

frontend/
  index.html             # 完整对话 UI

run_web.py               # Web 服务入口
pyproject.toml           # uv 依赖管理
README.md                # 使用文档
ARCHITECTURE.md          # 本文件
```

## 核心优势

✅ **deepagents**：使用 `create_deep_agent`，同时支持 middleware + checkpoint  
✅ **Skills 自动注入**：SkillsMiddleware 根据上下文智能推荐技能  
✅ **多轮对话支持**：Checkpoint 自动恢复状态  
✅ **可扩展**：工具独立，middleware 可插拔，backend 可替换  
✅ **可维护**：结构清晰，职责明确，符合 SOLID 原则  
