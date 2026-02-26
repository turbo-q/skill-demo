---
id: web_basic_scan
name: web-basic-scan
description: 基础 Web 漏洞扫描流程。适用于对单个 Web 站点进行初步安全扫描。
tags:
  - web
  - vuln
  - scan
# 技能绑定工具（主流 Skill = 说明 + 工具 + 可选脚本）
tools:
  - tcp_port_scan
  - http_get
# 可选：技能目录内可执行脚本，由 invoke_skill 调用
script: scripts/checklist.py
---

# 基础 Web 漏洞扫描流程

1. 识别目标：确认域名/IP 和授权范围。
2. 端口探测：优先扫描 80/443/8080/8443 等常见 Web 端口以及 22/3306/6379 等高危端口。
3. 指纹识别：通过 HTTP 响应头和页面特征识别中间件和框架（Server、X-Powered-By 等）。
4. 常见漏洞测试：SQL 注入、XSS、弱口令、敏感信息泄露等，可结合自动化扫描工具与手工验证。
5. 记录所有请求和响应（URL、参数、状态码、响应体关键片段），形成可复现的测试报告。

