from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class SkillModel(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text())
    content: Mapped[str] = mapped_column(Text())
    tags: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)


class SessionModel(Base):
    """会话表。"""
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_: Mapped[str] = mapped_column("metadata", Text(), default="{}")


class ConversationMessageModel(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)


class LlmConfigModel(Base):
    """模型配置表，单行存储（id=1）。"""
    __tablename__ = "llm_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # 固定 1
    model: Mapped[str] = mapped_column(String(128), default="gpt-4.1-mini")
    api_key: Mapped[str] = mapped_column(Text(), default="")
    base_url: Mapped[str] = mapped_column(String(512), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)


class UserModel(Base):
    """用户表。"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)


class UserSessionModel(Base):
    """用户登录会话，用于简单的基于 token 的登录态。"""
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

