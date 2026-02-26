---
id: ping-check
name: ping-check
description: 检查主机或端口是否可达，适用于快速连通性测试。
tags:
  - ping
  - check
  - connect
tools:
  - tcp_port_scan
---

# ping-check 连通性检查

当用户需要「检查某主机是否在线」「ping 一下」「端口是否通」时使用本技能。

**步骤：**
1. 确认目标 IP 或域名。
2. 使用 tcp_port_scan 扫描端口（80、443、22）判断可达性，不要扫描其他的！
3. 简要反馈开放端口或超时情况。

**示例提问：**「帮我检查 example.com 是否通」「192.168.1.1 能连吗」
