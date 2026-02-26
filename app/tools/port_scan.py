"""
TCP 端口扫描工具：对目标主机进行基础端口探测，用于漏洞排查。
"""

from __future__ import annotations

import asyncio
import socket
from typing import List

from langchain_core.tools import BaseTool


class PortScanTool(BaseTool):
    """对目标主机进行基础 TCP 端口扫描，仅用于授权安全测试。"""

    name: str = "tcp_port_scan"
    description: str = (
        "对目标主机进行基础 TCP 端口扫描，用于漏洞排查。"
        "输入参数为 target_host:str 和 ports:list[int]，只用于安全测试。"
    )

    def _run(self, target_host: str, ports: List[int]) -> str:  # type: ignore[override]
        open_ports: List[int] = []
        for port in ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    s.connect((target_host, port))
                    open_ports.append(port)
            except OSError:
                continue
        if open_ports:
            return f"开放端口: {sorted(open_ports)}"
        return "未发现开放端口（在当前端口列表内）。"

    async def _arun(self, target_host: str, ports: List[int]) -> str:  # type: ignore[override]
        return await asyncio.to_thread(self._run, target_host, ports)
