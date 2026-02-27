from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import UserModel, UserSessionModel


PASSWORD_MIN_LENGTH = 6
SESSION_TTL_HOURS = 72
AUTH_COOKIE_NAME = "auth_token"


def hash_password(raw: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw.encode("utf-8"), salt).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_session(db: Session, user: UserModel) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires = now + timedelta(hours=SESSION_TTL_HOURS)
    s = UserSessionModel(user_id=user.id, token=token, created_at=now, expires_at=expires)
    db.add(s)
    db.flush()
    return token


def get_user_by_token(db: Session, token: str) -> Optional[UserModel]:
    if not token:
        return None
    now = datetime.utcnow()
    session = (
        db.query(UserSessionModel)
        .filter(UserSessionModel.token == token, UserSessionModel.expires_at > now)
        .one_or_none()
    )
    if not session:
        return None
    user = db.query(UserModel).get(session.user_id)
    return user


async def get_current_user(
    auth_token: Optional[str] = Cookie(default=None, alias=AUTH_COOKIE_NAME),
    db: Session = Depends(get_db_session),
) -> UserModel:
    user = get_user_by_token(db, auth_token or "")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    return user


def set_auth_cookie(resp: Response, token: str) -> None:
    secure = os.environ.get("AUTH_COOKIE_SECURE", "false").lower() == "true"
    resp.set_cookie(
        AUTH_COOKIE_NAME,
        token,
        httponly=True,
        secure=secure,
        samesite="lax",
        max_age=SESSION_TTL_HOURS * 3600,
        path="/",
    )


def clear_auth_cookie(resp: Response) -> None:
    resp.delete_cookie(AUTH_COOKIE_NAME, path="/")

