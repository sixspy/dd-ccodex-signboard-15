"""登录与角色。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from models import USERS

router = APIRouter(prefix="/api/auth", tags=["auth"])
SESSIONS: dict[str, str] = {}


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    token = authorization.removeprefix("Bearer ").strip()
    username = SESSIONS.get(token)
    if not username or username not in USERS:
        raise HTTPException(401, "会话失效")
    u = USERS[username]
    return {"username": username, "role": u["role"], "display": u["display"]}


def require_writer(user: dict) -> None:
    if user["role"] not in ("admin", "writer"):
        raise HTTPException(403, "只读账号不可写入")


@router.post("/login")
def login(body: dict):
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    u = USERS.get(username)
    if not u or u["password"] != password:
        raise HTTPException(401, "用户名或密码错误")
    token = f"tok-{username}-{u['role']}"
    SESSIONS[token] = username
    return {
        "token": token,
        "username": username,
        "role": u["role"],
        "display": u["display"],
    }


@router.get("/me")
def me(authorization: str | None = Header(default=None)):
    return current_user(authorization)
