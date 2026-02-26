# Skill 是什么

**Skill 不是单纯的「提示词」**，而是**可执行的专业技能包**，是 Agent 的能力单元。

## 常见形态

- 每个 skill 一个**文件夹**，内含 SKILL.md（元信息 + 说明）、可选 configs/、scripts/、references/ 等，即 **元数据 + 说明 + 可选可执行环境（脚本/子 Agent/工作流）**。

## 本项目实现

- **SKILL.md front-matter 扩展**：
  - `tools`：该技能绑定的工具名列表（如 `tcp_port_scan`, `http_get`, `execute`），用于推荐/限定工具。
  - `script`：技能目录内可执行脚本相对路径（如 `scripts/checklist.py`），由 Agent 通过 **execute** 在技能目录下执行。
  - `config`：预留（如 `configs/agent.yaml`）子 Agent/工作流配置。
- **能力**：
  - **提示块**：SkillsMiddleware 按需将技能说明注入 system prompt，并展示「绑定工具」。
  - **执行脚本**：使用 deepagents 官方 **LocalShellBackend**，Agent 拥有 **execute** 工具；工作目录为项目根，请用**相对路径**直接执行脚本（不要用 cd、不要用 /app），例如 `SKILL_CONTEXT='{"target":"..."}' python3 app/skills/scan-report/scripts/generate_template.py`。
- **目录结构示例**：`web_basic_scan/SKILL.md`、`web_basic_scan/scripts/checklist.py`，可选 `configs/`、`references/`。

这样 Skill = **元数据 + 说明 + 绑定工具 + 可选可执行脚本**，与主流「可执行技能包」一致。
