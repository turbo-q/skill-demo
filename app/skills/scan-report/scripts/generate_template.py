#!/usr/bin/env python3
"""
技能可执行脚本示例：输出漏洞扫描报告模板。
由 execute 在技能目录下执行，SKILL_CONTEXT 可通过环境变量传入 JSON。
"""

import json
import os
import sys


def main() -> None:
    context = {}
    raw = os.environ.get("SKILL_CONTEXT")
    if raw:
        try:
            context = json.loads(raw)
        except Exception:
            pass

    target = context.get("target") or context.get("target_url") or context.get("target_host") or "目标"
    scan_type = context.get("scan_type") or "综合"
    lines = [
        f"# 漏洞扫描报告 — {target}",
        "",
        f"**扫描类型**: {scan_type}",
        "**生成说明**: 由技能 scan-report 脚本生成，以下为报告结构模板。",
        "",
        "---",
        "",
        "## 1. 概述",
        "- 目标信息",
        "- 扫描时间与范围",
        "- 执行摘要",
        "",
        "## 2. 资产与端口",
        "- 开放端口列表",
        "- 服务指纹",
        "",
        "## 3. 漏洞与风险",
        "| 序号 | 风险等级 | 描述 | 位置/证据 | 修复建议 |",
        "|------|----------|------|-----------|----------|",
        "",
        "## 4. 附录",
        "- 请求/响应关键片段",
        "- 复现步骤",
        "",
        "---",
        "*以上为报告模板，请根据实际扫描结果填写。*",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
    sys.exit(0)
