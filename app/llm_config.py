"""
模型配置读写：从 llm_config 表读取/写入，对话时由 run() 使用。
并根据 api_key / base_url 从 OpenAI 兼容接口拉取模型列表。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.db import get_session
from app.models import LlmConfigModel


CONFIG_ID = 1
DEFAULT_MODEL = "gpt-4.1-mini"


@dataclass
class LlmConfig:
    model: str
    api_key: str
    base_url: str


def get_llm_config() -> LlmConfig:
    """从数据库读取当前模型配置，若不存在则插入默认行并返回。"""
    with get_session() as session:
        row = session.get(LlmConfigModel, CONFIG_ID)
        if row is None:
            row = LlmConfigModel(
                id=CONFIG_ID,
                model=DEFAULT_MODEL,
                api_key="",
                base_url="",
            )
            session.add(row)
            session.flush()
        return LlmConfig(
            model=row.model or DEFAULT_MODEL,
            api_key=row.api_key or "",
            base_url=(row.base_url or "").strip(),
        )


def set_llm_config(
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LlmConfig:
    """更新模型配置（只更新传入的字段），返回最新配置。"""
    with get_session() as session:
        row = session.get(LlmConfigModel, CONFIG_ID)
        if row is None:
            row = LlmConfigModel(
                id=CONFIG_ID,
                model=DEFAULT_MODEL,
                api_key="",
                base_url="",
            )
            session.add(row)
            session.flush()
        if model is not None:
            row.model = model
        if api_key is not None:
            row.api_key = api_key
        if base_url is not None:
            row.base_url = base_url.strip()
        session.flush()
        return LlmConfig(
            model=row.model or DEFAULT_MODEL,
            api_key=row.api_key or "",
            base_url=(row.base_url or "").strip(),
        )


def fetch_models_from_provider(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[str]:
    """
    使用给定的 base_url 和 api_key 调用 OpenAI 兼容的 GET /models，返回模型 id 列表。
    base_url 为空时使用 https://api.openai.com/v1；
    api_key 为空时使用环境变量 OPENAI_API_KEY。
    """
    url_base = (base_url or "").strip() or "https://api.openai.com/v1"
    key = (api_key or "").strip() or os.environ.get("OPENAI_API_KEY") or ""
    url = f"{url_base.rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {key}"} if key else {}

    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        raise ValueError(f"获取模型列表失败: {e}") from e

    models = data.get("data") or []
    ids = [m.get("id") for m in models if isinstance(m, dict) and m.get("id")]
    return sorted(ids)
