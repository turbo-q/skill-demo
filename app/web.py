"""
对话后端：FastAPI + 完整 Agent UI（frontend/ 静态页）。
存储与对话走 run()；API：/api/chat、/api/sessions、/api/history。
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db import init_db
from app.run import run
from app.storage import get_storage_manager, initialize_storage

init_db()

# 确保 callback/run 日志在 uvicorn reload 子进程里也输出（子进程不会执行 run_web.main）
_log_level = logging.DEBUG if os.environ.get("LOG_LEVEL") == "DEBUG" else logging.INFO
logging.basicConfig(level=_log_level, format="%(levelname)s %(name)s %(message)s")
for _name in ("app.callbacks", "app.run"):
    logging.getLogger(_name).setLevel(_log_level)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_storage()
    yield


app = FastAPI(
    title="漏洞扫描 Agent",
    description="Skill + Tools + StorageManager + 完整 UI",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tool_calls: list = []  # [{"tool": "tcp_port_scan", "input": {...}, "output": "..."}]


class LlmConfigResponse(BaseModel):
    model: str
    base_url: str
    api_key_set: bool  # 是否已配置 key（不返回明文）


class LlmConfigUpdate(BaseModel):
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    if not (body.message or "").strip():
        raise HTTPException(status_code=400, detail="message 不能为空")
    metadata = {
        "session_id": body.session_id,
        "user_id": body.user_id or "default",
    }
    session_id, reply, tool_calls = await run(body.message.strip(), metadata)
    return ChatResponse(session_id=session_id, reply=reply, tool_calls=tool_calls)


@app.get("/api/config", response_model=LlmConfigResponse)
async def get_config():
    """获取当前模型配置（api_key 只返回是否已设置）。"""
    from app.llm_config import get_llm_config
    c = get_llm_config()
    return LlmConfigResponse(
        model=c.model,
        base_url=c.base_url,
        api_key_set=bool(c.api_key),
    )


@app.put("/api/config")
async def update_config(body: LlmConfigUpdate):
    """更新模型配置（单独的表存储）。"""
    from app.llm_config import set_llm_config
    kwargs = {}
    if body.model is not None:
        kwargs["model"] = body.model
    if body.base_url is not None:
        kwargs["base_url"] = body.base_url
    if body.api_key is not None:
        kwargs["api_key"] = body.api_key
    c = set_llm_config(**kwargs)
    return {"model": c.model, "base_url": c.base_url, "api_key_set": bool(c.api_key)}


class ModelsRequest(BaseModel):
    """获取模型列表时可选传入凭证（不传则用已保存配置）。"""
    base_url: Optional[str] = None
    api_key: Optional[str] = None


@app.get("/api/config/models")
async def list_models_from_config():
    """根据已保存的 base_url / api_key 拉取模型列表。"""
    from app.llm_config import fetch_models_from_provider, get_llm_config
    c = get_llm_config()
    try:
        models = fetch_models_from_provider(base_url=c.base_url or None, api_key=c.api_key or None)
        return {"models": models}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/config/models")
async def list_models_with_credentials(body: ModelsRequest):
    """用当前传入的 base_url / api_key 拉取模型列表（不写入配置表）。"""
    from app.llm_config import fetch_models_from_provider, get_llm_config
    base_url = body.base_url
    api_key = body.api_key
    if base_url is None and api_key is None:
        c = get_llm_config()
        base_url = c.base_url or None
        api_key = c.api_key or None
    try:
        models = fetch_models_from_provider(base_url=base_url, api_key=api_key)
        return {"models": models}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions")
async def list_sessions(user_id: str = "default", limit: int = 20, offset: int = 0):
    storage = get_storage_manager()
    sessions, total = await storage.backend.list_user_sessions(user_id, limit=limit, offset=offset)
    return {"user_id": user_id, "total": total, "sessions": sessions}


@app.get("/api/history")
async def history(session_id: str, limit: int = 50):
    storage = get_storage_manager()
    messages = await storage.context.get_conversation_history(session_id, limit=limit)
    return {
        "session_id": session_id,
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
    }


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    from fastapi.responses import HTMLResponse
    @app.get("/", response_class=HTMLResponse)
    async def _fallback_index():
        return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>漏洞扫描 Agent</title></head><body>
        <p>未找到 frontend 目录，请从项目根运行并保留 <code>frontend/</code>。</p>
        <p><a href="/docs">API 文档</a></p></body></html>"""
