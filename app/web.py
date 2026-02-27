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

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.auth import (
    PASSWORD_MIN_LENGTH,
    clear_auth_cookie,
    create_session,
    get_current_user,
    hash_password,
    set_auth_cookie,
    verify_password,
)
from app.db import get_db_session, init_db
from app.run import run
from app.storage import get_storage_manager, initialize_storage
import yaml
from app.models import UserModel

init_db()

# 确保 callback/run 日志在 uvicorn reload 子进程里也输出（子进程不会执行 run_web.main）
_log_level = logging.DEBUG if os.environ.get("LOG_LEVEL") == "DEBUG" else logging.INFO
logging.basicConfig(level=_log_level, format="%(levelname)s %(name)s %(message)s")
for _name in ("app.callbacks", "app.run"):
    logging.getLogger(_name).setLevel(_log_level)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"


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
async def chat(body: ChatRequest, current_user: UserModel = Depends(get_current_user)):
    if not (body.message or "").strip():
        raise HTTPException(status_code=400, detail="message 不能为空")
    metadata = {
        "session_id": None,
        "user_id": current_user.username,
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


class SkillSummary(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str]


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthUserResponse(BaseModel):
    username: str


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


@app.post("/api/auth/register", response_model=AuthUserResponse)
async def register(body: AuthRequest, db=Depends(get_db_session)):
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    if len(body.password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=400, detail=f"密码长度至少为 {PASSWORD_MIN_LENGTH} 位")
    exists = db.query(UserModel).filter(UserModel.username == username).one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = UserModel(username=username, password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    return AuthUserResponse(username=user.username)


@app.post("/api/auth/login", response_model=AuthUserResponse)
async def login(body: AuthRequest, response: Response, db=Depends(get_db_session)):
    username = body.username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")
    user = db.query(UserModel).filter(UserModel.username == username).one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_session(db, user)
    set_auth_cookie(response, token)
    return AuthUserResponse(username=user.username)


@app.post("/api/auth/logout")
async def logout(response: Response, current_user: UserModel = Depends(get_current_user)):
    clear_auth_cookie(response)
    return {"ok": True}


@app.get("/api/auth/me", response_model=AuthUserResponse)
async def me(current_user: UserModel = Depends(get_current_user)):
    return AuthUserResponse(username=current_user.username)


@app.get("/api/sessions")
async def list_sessions(limit: int = 20, offset: int = 0, current_user: UserModel = Depends(get_current_user)):
    storage = get_storage_manager()
    sessions, total = await storage.backend.list_user_sessions(current_user.username, limit=limit, offset=offset)
    return {"user_id": current_user.username, "total": total, "sessions": sessions}


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user: UserModel = Depends(get_current_user)):
    """删除该会话及其全部消息，彻底清除。仅当会话属于当前用户时允许删除。"""
    storage = get_storage_manager()
    ctx = await storage.context.get_session(session_id)
    if not ctx or ctx.user_id != current_user.username:
        raise HTTPException(status_code=404, detail="会话不存在")
    ok = await storage.backend.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"deleted": session_id}


@app.get("/api/history")
async def history(session_id: str, limit: int = 50, current_user: UserModel = Depends(get_current_user)):
    storage = get_storage_manager()
    ctx = await storage.context.get_session(session_id)
    if not ctx or ctx.user_id != current_user.username:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = await storage.context.get_conversation_history(session_id, limit=limit)
    return {
        "session_id": session_id,
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
    }


@app.get("/api/skills", response_model=list[SkillSummary])
async def list_skills(current_user: UserModel = Depends(get_current_user)) -> list[SkillSummary]:
    """从 app/skills 目录读取 SKILL.md，返回技能列表（不依赖数据库）。需要登录。"""
    skills_dir = Path(__file__).resolve().parent / "skills"
    results: list[SkillSummary] = []
    if not skills_dir.is_dir():
        return results

    for child in sorted(skills_dir.iterdir()):
        skill_file = child / "SKILL.md"
        if not skill_file.is_file():
            continue
        text = skill_file.read_text(encoding="utf-8")
        # 解析 YAML front-matter
        meta: dict = {}
        if text.lstrip().startswith("---"):
            try:
                _, rest = text.split("---", 1)
                yaml_part, *_ = rest.split("---", 1)
                meta = yaml.safe_load(yaml_part) or {}
            except Exception:
                meta = {}

        sid = str(meta.get("id") or child.name)
        name = str(meta.get("name") or sid)
        desc = str(meta.get("description") or "").strip()
        raw_tags = meta.get("tags") or []
        if isinstance(raw_tags, str):
            tags = [t for t in (x.strip() for x in raw_tags.split(",")) if t]
        elif isinstance(raw_tags, (list, tuple)):
            tags = [str(t) for t in raw_tags if str(t).strip()]
        else:
            tags = []

        results.append(
            SkillSummary(
                id=sid,
                name=name,
                description=desc,
                tags=tags,
            )
        )
    return results


if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
else:
    from fastapi.responses import HTMLResponse

    @app.get("/", response_class=HTMLResponse)
    async def _fallback_index():
        return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>漏洞扫描 Agent</title></head><body>
        <p>未找到已构建的前端资源，请先执行 <code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code>。</p>
        <p><a href="/docs">API 文档</a></p></body></html>"""

