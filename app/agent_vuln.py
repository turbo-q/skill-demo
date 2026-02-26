"""
漏洞扫描 Agent 实现。

核心设计：
- 使用 deepagents.create_deep_agent（同时支持 middleware + checkpoint）
- Skills 由 deepagents.middleware.skills.SkillsMiddleware 自动管理
- Checkpoint 由 LangGraph MemorySaver 提供
- 工具从 app.tools 统一注册
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.skills import SkillsMiddleware
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver

from app.tools import build_vuln_scan_tools


BASE_SYSTEM_PROMPT = """
你是一个专业的漏洞扫描与安全分析智能体，职责包括：
- 根据目标资产信息（域名 / IP / URL）制定渗透测试/漏洞扫描计划。
- 合理调用端口扫描、HTTP 探测等工具，避免无意义的大规模扫描。
- 严格限制在授权范围内，只做用户明确授权的安全测试。
- 输出结果时，给出：
  1）发现的风险点
  2）对应的技术细节（端口、URL、HTTP 细节等）
  3）漏洞成因分析
  4）修复建议（面向开发和运维）

使用工具时：
- 优先用 tcp_port_scan 识别开放端口，再针对性用 http_get 分析 Web 服务。
- 技能知识会根据上下文自动注入，请结合技能说明和工具验证。
"""


def get_agent(
    llm_model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    system_prompt: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    checkpointer: Optional[Any] = None,
) -> Any:
    """
    构建漏洞扫描 Agent。
    api_key / base_url 为空时使用环境变量（如 OPENAI_API_KEY）。
    """
    model_name = llm_model or "gpt-4.1-mini"

    default_tools: List[BaseTool] = build_vuln_scan_tools()
    all_tools: List[Any] = default_tools.copy()
    if tools:
        all_tools.extend(tools)

    final_system_prompt = system_prompt or BASE_SYSTEM_PROMPT.strip()

    if checkpointer is None:
        checkpointer = MemorySaver()

    # 项目根目录：read_file 等文件工具可访问项目下所有路径
    project_root = Path(__file__).resolve().parent.parent
    backend = FilesystemBackend(root_dir=str(project_root))
    # 技能从 app/skills 加载（相对 project_root）
    skills_middleware = SkillsMiddleware(backend=backend, sources=["app/skills"])

    model_arg: Any = model_name
    if api_key or base_url:
        from langchain_openai import ChatOpenAI
        kwargs = {"model": model_name, "temperature": 0.1}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url.rstrip("/")
        model_arg = ChatOpenAI(**kwargs)

    agent = create_deep_agent(
        model=model_arg,
        tools=all_tools,
        system_prompt=final_system_prompt,
        middleware=[skills_middleware],
        checkpointer=checkpointer,
        backend=backend,
    )
    return agent


