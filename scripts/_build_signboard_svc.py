# -*- coding: utf-8 -*-
"""signboard 后端服务源码常量。"""
from __future__ import annotations

AUTH = r'''
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
'''

VALIDATORS = r'''
"""字段与业务校验。"""
from __future__ import annotations

import re
from fastapi import HTTPException

from models import (
    ASSET_KINDS,
    ASSET_STATUS,
    OVERRIDE_EFFECT,
    PLAYLIST_STATUS,
    SCREEN_STATUS,
    TRANSITION_KINDS,
    WINDOW_STATUS,
    ZONE_TYPES,
)

CODE_RE = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
HM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def require_code(code: str, label: str = "编码") -> str:
    code = (code or "").strip()
    if not CODE_RE.match(code):
        raise HTTPException(400, f"{label}须为小写字母开头的短码")
    return code


def require_title(title: str, label: str = "标题") -> str:
    title = (title or "").strip()
    if len(title) < 2 or len(title) > 80:
        raise HTTPException(400, f"{label}长度须在 2～80")
    return title


def require_kind(kind: str) -> str:
    if kind not in ASSET_KINDS:
        raise HTTPException(400, "素材种类不合法")
    return kind


def require_asset_status(status: str) -> str:
    if status not in ASSET_STATUS:
        raise HTTPException(400, "素材状态不合法")
    return status


def require_screen_status(status: str) -> str:
    if status not in SCREEN_STATUS:
        raise HTTPException(400, "屏幕状态不合法")
    return status


def require_playlist_status(status: str) -> str:
    if status not in PLAYLIST_STATUS:
        raise HTTPException(400, "清单状态不合法")
    return status


def require_window_status(status: str) -> str:
    if status not in WINDOW_STATUS:
        raise HTTPException(400, "时段窗状态不合法")
    return status


def require_zone_type(zone_type: str) -> str:
    if zone_type not in ZONE_TYPES:
        raise HTTPException(400, "分区类型不合法")
    return zone_type


def require_transition(transition: str) -> str:
    if transition not in TRANSITION_KINDS:
        raise HTTPException(400, "过渡方式不合法")
    return transition


def require_effect(effect: str) -> str:
    if effect not in OVERRIDE_EFFECT:
        raise HTTPException(400, "覆盖效果不合法")
    return effect


def require_hm(hm: str, label: str) -> str:
    hm = (hm or "").strip()
    if not HM_RE.match(hm):
        raise HTTPException(400, f"{label}须为 HH:MM")
    return hm


def require_weekdays(weekdays: str) -> str:
    weekdays = (weekdays or "").strip()
    parts = [p for p in weekdays.split(",") if p]
    if not parts:
        raise HTTPException(400, "星期集合不能为空")
    for p in parts:
        if p not in {"1", "2", "3", "4", "5", "6", "7"}:
            raise HTTPException(400, "星期须为 1～7")
    return ",".join(sorted(set(parts), key=int))


def require_positive_int(value, label: str, lo: int = 1, hi: int = 86400) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, f"{label}须为整数")
    if n < lo or n > hi:
        raise HTTPException(400, f"{label}超出范围")
    return n


def hm_to_min(hm: str) -> int:
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def window_covers(start_hm: str, end_hm: str, now_hm: str) -> bool:
    s, e, n = hm_to_min(start_hm), hm_to_min(end_hm), hm_to_min(now_hm)
    if s == e:
        return True
    if s < e:
        return s <= n < e
    return n >= s or n < e
'''

POLICIES = r'''
"""写入策略与风险闸。"""
from __future__ import annotations

from fastapi import HTTPException


def assert_zone_risk_for_outdoor(zone_type: str, risk_level: int) -> None:
    if zone_type == "outdoor" and risk_level < 3:
        raise HTTPException(400, "室外分区风险等级至少为 3")


def assert_playlist_ready(status: str) -> None:
    if status != "ready":
        raise HTTPException(409, "仅可播清单可发布上屏")


def assert_window_open(status: str) -> None:
    if status != "open":
        raise HTTPException(409, "时段窗未开放，禁止发布")


def assert_screen_online(status: str) -> None:
    if status == "maintenance":
        raise HTTPException(409, "维保中的屏幕禁止发布")


def assert_asset_ready(status: str) -> None:
    if status != "ready":
        raise HTTPException(409, "仅可播素材可进入清单")


def assert_resolution_compatible(screen_res: str, asset_res: str) -> None:
    if screen_res != asset_res and not asset_res.startswith(screen_res.split("x")[0]):
        # 允许同宽不同高的宽松匹配；完全无关则拒绝
        sw = screen_res.split("x")[0]
        aw = asset_res.split("x")[0]
        if sw != aw:
            raise HTTPException(409, "素材分辨率与屏幕不兼容")


def assert_override_payload(effect: str, playlist_id, asset_id) -> None:
    if effect == "force_playlist" and not playlist_id:
        raise HTTPException(400, "强制清单须指定清单")
    if effect == "force_asset" and not asset_id:
        raise HTTPException(400, "强制单素材须指定素材")
    if effect == "force_blank" and (playlist_id or asset_id):
        raise HTTPException(400, "强制空屏不得附带清单或素材")


POLICY_NOTES = [
    "客户可见区发布须有变更历史可追溯",
    "紧急撤屏后正式发布版本不得静默回写",
    "单屏覆盖激活时求值优先覆盖条目",
    "影子草案升正前正式区零改",
    "维保屏幕只允许查看不可发布",
]
'''

LOCKS = r'''
"""写入短锁，防并发双写。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from auth import current_user, require_writer
from db import connect

router = APIRouter(prefix="/api/locks", tags=["locks"])


def acquire(lock_key: str, holder: str, ttl_sec: int = 20) -> None:
    now = time.time()
    with connect() as conn:
        row = conn.execute(
            "SELECT holder, expires_at FROM write_locks WHERE lock_key=?",
            (lock_key,),
        ).fetchone()
        if row and row["expires_at"] > now and row["holder"] != holder:
            raise HTTPException(409, f"资源锁定中：{row['holder']}")
        conn.execute(
            "INSERT INTO write_locks(lock_key,holder,expires_at) VALUES(?,?,?) "
            "ON CONFLICT(lock_key) DO UPDATE SET holder=excluded.holder, expires_at=excluded.expires_at",
            (lock_key, holder, now + ttl_sec),
        )
        conn.commit()


def release(lock_key: str, holder: str) -> None:
    with connect() as conn:
        conn.execute(
            "DELETE FROM write_locks WHERE lock_key=? AND holder=?",
            (lock_key, holder),
        )
        conn.commit()


@router.post("/acquire")
def api_acquire(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    key = (body.get("lock_key") or "").strip()
    if not key:
        raise HTTPException(400, "缺少 lock_key")
    acquire(key, user["username"], int(body.get("ttl_sec") or 20))
    return {"ok": True, "lock_key": key, "holder": user["username"]}


@router.post("/release")
def api_release(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    key = (body.get("lock_key") or "").strip()
    release(key, user["username"])
    return {"ok": True}
'''

AUDIT = r'''
"""审计与辅助查询。"""
from __future__ import annotations

import json
import time
from fastapi import APIRouter, Header

from auth import current_user
from db import connect, rows_to_list

router = APIRouter(prefix="/api/audit", tags=["audit"])


def write_audit(actor: str, action: str, payload: dict) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(actor,action,payload,created_at) VALUES(?,?,?,?)",
            (actor, action, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        conn.commit()


def write_history(entity_kind: str, entity_id: int, action: str, detail: str, actor: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO change_history(entity_kind,entity_id,action,detail,actor,created_at) VALUES(?,?,?,?,?,?)",
            (entity_kind, entity_id, action, detail, actor, time.time()),
        )
        conn.commit()


@router.get("/recent")
def recent(limit: int = 50, authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 200)),),
        ).fetchall()
    return {"items": rows_to_list(rows)}
'''
