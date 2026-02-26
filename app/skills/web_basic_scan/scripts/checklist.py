#!/usr/bin/env python3
"""
技能可执行脚本示例：输出「基础 Web 扫描」检查清单。
由 invoke_skill(skill_id, context) 调用，SKILL_CONTEXT 可通过环境变量传入 JSON。
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

    target = context.get("target_url") or context.get("target_host") or "目标"
    lines = [
        f"【基础 Web 漏洞扫描检查清单】针对 {target}",
        "",
        "1. 识别目标与授权范围",
        "2. 端口探测：80/443/8080/8443、22/3306/6379 等",
        "3. 指纹识别：Server、X-Powered-By、前端框架",
        "4. 常见漏洞：SQL 注入、XSS、弱口令、敏感信息泄露",
        "5. 记录请求/响应，形成可复现报告",
        "",
        "推荐工具：tcp_port_scan、http_get（可与本技能绑定一起使用）。",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()
    sys.exit(0)
