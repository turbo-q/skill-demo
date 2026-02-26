"""
漏洞扫描 Agent 所用工具统一入口。

核心工具：
- PortScanTool: TCP 端口扫描
- HttpGetTool: HTTP 探测

技能管理通过 deepagents.middleware.skills.SkillsMiddleware 自动处理，
不需要单独的技能工具。
"""

from __future__ import annotations

from typing import List

from langchain_core.tools import BaseTool

from app.tools.http_get import HttpGetTool
from app.tools.port_scan import PortScanTool


def build_vuln_scan_tools() -> List[BaseTool]:
    """构建漏洞扫描 Agent 的核心工具列表。"""
    return [
        PortScanTool(),
        HttpGetTool(),
    ]


__all__ = [
    "PortScanTool",
    "HttpGetTool",
    "build_vuln_scan_tools",
]
