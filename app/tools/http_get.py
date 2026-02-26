"""
HTTP GET 探测工具：对目标 URL 发起请求，返回状态码、响应头与片段，用于安全分析。
网络异常时返回友好错误信息，避免未捕获异常导致 500。
"""

from __future__ import annotations

import asyncio
from typing import Optional

import httpx
from langchain_core.tools import BaseTool


def _format_http_error(url: str, e: Exception) -> str:
    """将网络/HTTP 异常格式化为工具返回的字符串。"""
    msg = str(e).strip() or type(e).__name__
    return f"请求失败 [{url}]: {msg}\n（目标可能不可达、超时、或主动断开连接，请换目标或稍后重试。）"


class HttpGetTool(BaseTool):
    """对目标 URL 发起 HTTP GET 请求，返回状态码、响应头和部分 Body。"""

    name: str = "http_get"
    description: str = (
        "对目标 URL 发起 HTTP GET 请求，返回状态码、响应头和部分 Body，用于安全分析。"
        "入参为 url:str，可选 timeout:float。"
    )

    async def _arun(self, url: str, timeout: float = 10.0) -> str:  # type: ignore[override]
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                resp = await client.get(url, timeout=timeout)
                body_snippet = resp.text[:2000]
                return (
                    f"URL: {url}\n"
                    f"Status: {resp.status_code}\n"
                    f"Headers: {dict(resp.headers)}\n"
                    f"Body snippet (前 2000 字符):\n{body_snippet}"
                )
        except (httpx.HTTPError, OSError, asyncio.TimeoutError) as e:
            return _format_http_error(url, e)
        except Exception as e:
            return _format_http_error(url, e)

    def _run(self, url: str, timeout: float = 10.0) -> str:  # type: ignore[override]
        try:
            return asyncio.run(self._arun(url, timeout))
        except (httpx.HTTPError, OSError, asyncio.TimeoutError) as e:
            return _format_http_error(url, e)
        except Exception as e:
            return _format_http_error(url, e)
