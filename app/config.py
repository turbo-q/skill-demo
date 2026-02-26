from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 默认使用本地 SQLite 数据库，方便 demo 和开发
DATABASE_URL = f"sqlite:///{BASE_DIR / 'data.db'}"

