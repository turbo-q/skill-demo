"""
StorageManager：持有 backend + context。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.storage.context_manager import ContextManager

if TYPE_CHECKING:
    from app.storage.backend import PersistenceBackend


class StorageManager:
    """统一存储入口：backend + context。"""

    def __init__(self, backend: "PersistenceBackend") -> None:
        self.backend = backend
        self.context = ContextManager(backend)
