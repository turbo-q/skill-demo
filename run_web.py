"""
启动对话 UI 服务：FastAPI + 完整 frontend。
用 uv 运行：uv run web 或 uv run python run_web.py

查看「发给模型的 prompt」和「工具调用」日志：
  - 默认 INFO：会打 LLM 调用摘要、工具名与入参/结果摘要。
  - 完整 prompt（含技能注入内容）：LOG_LEVEL=DEBUG uv run web
"""
import logging
import os
import uvicorn


def main() -> None:
    level = logging.DEBUG if os.environ.get("LOG_LEVEL") == "DEBUG" else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("app.callbacks").setLevel(level)

    uvicorn.run("app.web:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
