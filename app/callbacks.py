"""
Agent 可观测：通过 LangChain callback 打日志，便于查看「发给模型的 prompt」和「工具调用」。
日志格式为人类可读的中文，便于直接阅读终端输出。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

# 确保本 logger 至少有一个 handler（uvicorn 子进程可能未执行 run_web.main）
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s %(name)s %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

# 每条日志单行最大长度，超出截断
_MAX_LOG_LINE = 400


def _to_str(obj: Any) -> str:
    """将 output 转为字符串（可能是 ToolMessage 等对象）。"""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "content"):
        c = getattr(obj, "content", None)
        return c if isinstance(c, str) else str(c)
    return str(obj)


def _truncate(s: str, max_len: int = _MAX_LOG_LINE) -> str:
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[:max_len] + "…"


def _message_summary(msg: BaseMessage) -> str:
    role = getattr(msg, "type", None) or type(msg).__name__
    content = getattr(msg, "content", None)
    if content is None:
        return f"[{role}]"
    s = _to_str(content)
    return f"[{role}] {_truncate(s, 120)}"


def _messages_prompt_string(messages: List[BaseMessage]) -> str:
    parts = []
    for m in messages:
        role = getattr(m, "type", None) or type(m).__name__
        content = getattr(m, "content", None)
        if content:
            parts.append(f"========== {role} ==========\n{content}")
        else:
            parts.append(f"========== {role} ==========\n(无内容)")
    return "\n".join(parts)


class PromptLoggingHandler(AsyncCallbackHandler):
    """
    人类可读的 prompt/工具 日志：
    - INFO：本次请求消息数、工具名与入参/返回（截断后单行或少量行）；
    - DEBUG：完整发给模型的 prompt（含技能注入）。
    """

    def __init__(self, log_prompt_at_debug: bool = True):
        self.log_prompt_at_debug = log_prompt_at_debug
        super().__init__()

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        for batch in messages:
            n = len(batch)
            first_preview = _message_summary(batch[0]) if batch else "（无消息）"
            logger.info(
                "【本次请求】发给模型的消息共 %s 条，首条摘要：%s",
                n,
                first_preview,
            )
            if self.log_prompt_at_debug and logger.isEnabledFor(logging.DEBUG):
                full = _messages_prompt_string(batch)
                logger.debug("【完整 prompt】\n%s", full)

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("name", "?")
        inp = _to_str(input_str)
        logger.info("【工具调用】%s 入参：%s", name, _truncate(inp, 300))

    async def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        out_str = _to_str(output)
        logger.info("【工具返回】%s", _truncate(out_str))

    async def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        logger.warning("【工具报错】%s", error)
    

def get_prompt_logging_handler() -> PromptLoggingHandler:
    return PromptLoggingHandler(log_prompt_at_debug=True)
