"""
存储层：StorageManager + ContextManager + Backend。

- Backend：持久化后端（本实现为 SQLite）
- ContextManager：会话上下文（create_session, get_session, add_message, get_conversation_history）
- StorageManager：统一入口，持有 backend + context
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from app.db import SessionLocal, init_db
from app.storage.backend import SQLiteBackend, SessionContext
from app.storage.context_manager import ContextManager
from app.storage.storage_manage import StorageManager

_storage: Optional[StorageManager] = None
_storage_lock = asyncio.Lock()


async def initialize_storage() -> StorageManager:
    """应用启动时调用一次，初始化存储。"""
    global _storage
    async with _storage_lock:
        if _storage is not None:
            return _storage
        init_db()
        backend = SQLiteBackend()
        await backend.initialize()
        _storage = StorageManager(backend=backend)
        return _storage


def get_storage_manager() -> StorageManager:
    """获取已初始化的 StorageManager（必须先调用 initialize_storage）。"""
    if _storage is None:
        raise RuntimeError("Storage not initialized. Call initialize_storage() first.")
    return _storage


__all__ = [
    "initialize_storage",
    "get_storage_manager",
    "StorageManager",
    "ContextManager",
    "SessionContext",
    "SQLiteBackend",
]
