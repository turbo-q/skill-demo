"""
持久化后端接口与 SQLite 实现。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.db import SessionLocal
from app.models import ConversationMessageModel, SessionModel


class PersistenceBackend(ABC):
    """持久化后端抽象，此处用 SQLite 实现。"""

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def save_context(self, context: "SessionContext") -> None:
        pass

    @abstractmethod
    async def load_context(self, session_id: str) -> Optional["SessionContext"]:
        pass

    @abstractmethod
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        pass

    @abstractmethod
    async def list_user_sessions(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话及其全部消息，彻底清除。返回是否删除成功（会话存在则成功）。"""
        pass


class SessionContext:
    """会话上下文，与 context_manager 中的 SessionContext 结构一致。"""
    __slots__ = ("session_id", "user_id", "created_at", "updated_at", "messages", "metadata")

    def __init__(
        self,
        session_id: str,
        user_id: str,
        created_at: datetime,
        updated_at: datetime,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.messages = messages or []
        self.metadata = metadata or {}


class SQLiteBackend(PersistenceBackend):
    """基于 SQLite + SQLAlchemy 的后端。"""

    def __init__(self) -> None:
        self._session_factory = SessionLocal

    async def initialize(self) -> None:
        pass

    @staticmethod
    async def _run_sync(fn, *args, **kwargs):
        import asyncio
        return await asyncio.to_thread(lambda: fn(*args, **kwargs))

    def _save_context_sync(self, context: SessionContext) -> None:
        session = self._session_factory()
        try:
            row = session.query(SessionModel).get(context.session_id)
            meta_str = json.dumps(context.metadata, ensure_ascii=False)
            if row:
                row.user_id = context.user_id
                row.updated_at = context.updated_at
                row.metadata_ = meta_str
            else:
                session.add(SessionModel(
                    session_id=context.session_id,
                    user_id=context.user_id,
                    created_at=context.created_at,
                    updated_at=context.updated_at,
                    metadata_=meta_str,
                ))
            session.commit()
        finally:
            session.close()

    def _load_context_sync(self, session_id: str) -> Optional[SessionContext]:
        session = self._session_factory()
        try:
            row = session.query(SessionModel).get(session_id)
            if not row:
                return None
            try:
                meta = json.loads(row.metadata_ or "{}")
            except Exception:
                meta = {}
            msgs = session.query(ConversationMessageModel).filter(
                ConversationMessageModel.session_id == session_id
            ).order_by(ConversationMessageModel.created_at.asc()).all()
            messages = [
                {
                    "message_id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.created_at.isoformat() if m.created_at else "",
                }
                for m in msgs
            ]
            return SessionContext(
                session_id=row.session_id,
                user_id=row.user_id,
                created_at=row.created_at,
                updated_at=row.updated_at,
                messages=messages,
                metadata=meta,
            )
        finally:
            session.close()

    def _add_message_sync(self, session_id: str, role: str, content: str, metadata: Optional[Dict]) -> int:
        session = self._session_factory()
        try:
            msg = ConversationMessageModel(session_id=session_id, role=role, content=content)
            session.add(msg)
            session.commit()
            session.refresh(msg)
            return msg.id
        finally:
            session.close()

    def _list_user_sessions_sync(self, user_id: str, limit: int, offset: int) -> tuple[List[Dict], int]:
        session = self._session_factory()
        try:
            q = session.query(SessionModel).filter(SessionModel.user_id == user_id).order_by(
                SessionModel.updated_at.desc()
            )
            total = q.count()
            rows = q.offset(offset).limit(limit).all()
            out = []
            for r in rows:
                cnt = session.query(ConversationMessageModel).filter(
                    ConversationMessageModel.session_id == r.session_id
                ).count()
                out.append({
                    "session_id": r.session_id,
                    "user_id": r.user_id,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                    "message_count": cnt,
                })
            return out, total
        finally:
            session.close()

    def _delete_session_sync(self, session_id: str) -> bool:
        session = self._session_factory()
        try:
            row = session.query(SessionModel).get(session_id)
            if not row:
                return False
            session.query(ConversationMessageModel).filter(
                ConversationMessageModel.session_id == session_id
            ).delete(synchronize_session=False)
            session.delete(row)
            session.commit()
            return True
        finally:
            session.close()

    async def delete_session(self, session_id: str) -> bool:
        return await self._run_sync(self._delete_session_sync, session_id)

    async def save_context(self, context: SessionContext) -> None:
        await self._run_sync(self._save_context_sync, context)

    async def load_context(self, session_id: str) -> Optional[SessionContext]:
        return await self._run_sync(self._load_context_sync, session_id)

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        return await self._run_sync(self._add_message_sync, session_id, role, content, metadata)

    async def list_user_sessions(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[List[Dict[str, Any]], int]:
        return await self._run_sync(self._list_user_sessions_sync, user_id, limit, offset)
