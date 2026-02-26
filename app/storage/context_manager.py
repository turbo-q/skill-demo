"""
会话上下文管理：create_session / get_session / add_message / get_conversation_history，
会话与消息生命周期管理。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.storage.backend import PersistenceBackend, SessionContext


class ContextManager:
    """会话上下文管理，委托给 PersistenceBackend。"""

    def __init__(self, backend: PersistenceBackend) -> None:
        self._backend = backend

    async def create_session(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionContext:
        sid = session_id or str(uuid.uuid4())
        now = datetime.utcnow()
        ctx = SessionContext(
            session_id=sid,
            user_id=user_id,
            created_at=now,
            updated_at=now,
            messages=[],
            metadata=metadata or {},
        )
        await self._backend.save_context(ctx)
        return ctx

    async def get_session(self, session_id: str) -> Optional[SessionContext]:
        return await self._backend.load_context(session_id)

    async def get_or_create_session(
        self,
        session_id: Optional[str],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionContext:
        if session_id:
            ctx = await self.get_session(session_id)
            if ctx is not None:
                return ctx
        return await self.create_session(user_id=user_id, session_id=session_id, metadata=metadata)

    async def update_session(
        self,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        ctx = await self._backend.load_context(session_id)
        if ctx is None:
            return
        ctx.updated_at = datetime.utcnow()
        if metadata is not None:
            ctx.metadata.update(metadata)
        await self._backend.save_context(ctx)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        return await self._backend.add_message(session_id, role, content, metadata)

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        ctx = await self._backend.load_context(session_id)
        if not ctx or not ctx.messages:
            return []
        return ctx.messages[-limit:]
