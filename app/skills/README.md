# Skill 是什么

**Skill 不是单纯的「提示词」**，而是**可执行的专业技能包**，是 Agent 的能力单元。

## 常见形态

- 每个 skill 一个**文件夹**，内含 SKILL.md（元信息 + 说明）、可选 configs/、scripts/、references/ 等，即 **元数据 + 说明 + 可选可执行环境（脚本/子 Agent/工作流）**。

## 本项目实现

- **SKILL.md front-matter 扩展**：
  - `tools`：该技能绑定的工具名列表（如 `tcp_port_scan`, `http_get`），用于推荐/限定工具。
  - `script`：技能目录内可执行脚本相对路径（如 `scripts/checklist.py`），由 `invoke_skill` 调用。
  - `config`：预留（如 `configs/agent.yaml`）子 Agent/工作流配置。
- **能力**：
  - **提示块**：`build_prompt_block` 仍按 query/tags 检索并拼成注入 system prompt 的文本，并在块中展示「绑定工具」。
  - **检索**：`security_skill_search` 按需拉取技能说明（Lazy RAG）。
  - **执行**：`invoke_skill(skill_id, context)` 若技能有 `script` 则运行脚本（可传 context），否则返回技能说明 + 推荐工具。
- **目录结构示例**：`web_basic_scan/SKILL.md`、`web_basic_scan/scripts/checklist.py`，可选 `configs/`、`references/`。

这样 Skill = **元数据 + 说明 + 绑定工具 + 可选可执行脚本**，与主流「可执行技能包」一致。
