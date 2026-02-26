---
id: scan_report
name: scan-report
description: 生成漏洞扫描报告模板。使用 execute 在技能目录下执行脚本即可输出结构化报告模板。
tags:
  - report
  - template
tools:
  - execute
script: scripts/generate_template.py
---

# 扫描报告模板技能

本技能提供「执行额外脚本」的示例：使用 **execute** 直接执行脚本。

## 使用方式

1. 用户请求「生成扫描报告模板」或「给我一份漏洞扫描报告格式」时，可选用本技能。
2. 使用 **execute** 执行，示例：
   `SKILL_CONTEXT='{"target":"example.com","scan_type":"web"}' python3 app/skills/scan-report/scripts/generate_template.py`
3. 脚本输出即为报告模板正文，可整理后返回给用户。
