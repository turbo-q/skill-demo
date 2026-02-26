"""
Agent 主流程。

流程：
1. init_storage → get/create session
2. 加载历史消息
3. add_message 用户输入
4. 调用 agent (checkpoint 自动恢复状态)
5. add_message assistant 回复
6. 返回 (session_id, reply, tool_calls)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agent_vuln import get_agent
from app.storage import get_storage_manager


def _extract_tool_calls(messages: List[Any]) -> List[Dict[str, Any]]:
    """从 agent 返回的 messages 中解析本轮的 tool 调用（名称、入参、结果）。"""
    out: List[Dict[str, Any]] = []
    pending: Dict[str, Dict[str, Any]] = {}  # id -> {tool, input, output}

    for msg in messages:
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tid = tc.get("id") or tc.get("tool_call_id") or ""
                name = tc.get("name") or ""
                args = tc.get("args") or {}
                pending[tid] = {"tool": name, "input": args, "output": None}
        tid = getattr(msg, "tool_call_id", None)
        if tid and tid in pending:
            content = getattr(msg, "content", None)
            pending[tid]["output"] = content if isinstance(content, str) else (str(content) if content is not None else "")
            out.append(pending[tid].copy())
            del pending[tid]

    return out


async def run(user_message: str, metadata: Dict[str, Any]) -> tuple[str, str, List[Dict[str, Any]]]:
    """
    单次对话执行。
    
    - metadata 需含 session_id（可选）、user_id
    - 若未提供 session_id 则创建新会话
    - 使用 LangGraph checkpoint 持久化对话状态
    - 返回 (session_id, reply)
    """
    from app.db import init_db
    init_db()

    storage = get_storage_manager()
    session_id: Optional[str] = metadata.get("session_id")
    user_id: str = metadata.get("user_id") or "default"

    ctx = await storage.context.get_or_create_session(
        session_id=session_id,
        user_id=user_id,
    )
    session_id = ctx.session_id

    await storage.context.add_message(session_id, "user", user_message)

    # 从「模型配置」表读取配置，构建 agent
    from app.llm_config import get_llm_config
    cfg = get_llm_config()
    graph = get_agent(
        llm_model=cfg.model,
        api_key=cfg.api_key or None,
        base_url=cfg.base_url or None,
    )

    # 加载历史消息
    history = await storage.context.get_conversation_history(session_id, limit=50)
    
    messages = []
    for m in history:
        messages.append((m["role"], m["content"]))
    messages.append(("user", user_message))

    import logging
    from app.callbacks import get_prompt_logging_handler

    handler = get_prompt_logging_handler()
    config = {
        "configurable": {"thread_id": session_id},
        "callbacks": [handler],
    }
    logging.getLogger("app.run").info("已注入 prompt/工具 日志 callback，请求 session=%s", session_id[:12] if session_id else "")

    # 调用 agent（checkpoint 会自动恢复状态；callback 会打 prompt/工具 日志）
    result = await graph.ainvoke({"messages": messages}, config=config)
    all_messages = result.get("messages") or []

    final_msg = all_messages[-1] if all_messages else None
    assistant_text = (final_msg.content if hasattr(final_msg, "content") else str(final_msg)) if final_msg else ""

    tool_calls = _extract_tool_calls(all_messages)

    await storage.context.add_message(session_id, "assistant", assistant_text)
    return session_id, assistant_text, tool_calls
