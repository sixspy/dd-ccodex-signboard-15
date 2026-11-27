"""紧急撤屏。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_contention, write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from locks import LockBusy, acquire, release
from validators import require_positive_int, require_title

router = APIRouter(prefix="/api/panic", tags=["panic"])


def _acquire_publish_lock(screen_id: int, user: dict, detail: str) -> str:
    lock_key = f"publish:{screen_id}"
    try:
        acquire(lock_key, user["username"])
    except LockBusy as exc:
        write_contention(
            "panic",
            screen_id,
            user["username"],
            f"紧急撤屏争用败方，整笔拒写：{detail}",
            {"lock_key": lock_key, "winner": exc.holder},
        )
        raise HTTPException(
            409,
            f"同屏正式发布互斥争用：{exc.holder} 持锁在途，撤屏整笔拒写且正式区零改",
        ) from exc
    return lock_key


@router.get("/events")
def list_events(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(
            conn.execute(
                """
                SELECT e.*, s.code screen_code, s.title screen_title
                FROM panic_events e JOIN screens s ON s.id=e.screen_id
                ORDER BY e.id DESC
                """
            ).fetchall()
        )
    return {"items": rows}


@router.get("/shadows")
def list_shadows(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(
            conn.execute(
                """
                SELECT sh.*, s.code screen_code
                FROM panic_shadows sh JOIN screens s ON s.id=sh.screen_id
                ORDER BY sh.id DESC
                """
            ).fetchall()
        )
    return {"items": rows}


@router.post("/official")
def panic_official(body: dict, authorization: str | None = Header(default=None)):
    """甲：同事务清空正式发布并记撤屏事件。"""
    user = current_user(authorization)
    require_writer(user)
    screen_id = require_positive_int(body.get("screen_id"), "屏幕编号")
    reason = require_title(body.get("reason") or "紧急撤屏", "原因")
    lock_key = _acquire_publish_lock(screen_id, user, reason)
    try:
        with connect() as conn:
            screen = conn.execute("SELECT * FROM screens WHERE id=?", (screen_id,)).fetchone()
            if not screen:
                raise HTTPException(404, "屏幕不存在")
            conn.execute(
                "UPDATE publications SET status='rolled_back' WHERE screen_id=? AND official=1",
                (screen_id,),
            )
            conn.execute("DELETE FROM publications WHERE screen_id=? AND official=1", (screen_id,))
            cur = conn.execute(
                "INSERT INTO panic_events(screen_id,reason,official,created_at,created_by) VALUES(?,?,?,?,?)",
                (screen_id, reason, 1, time.time(), user["username"]),
            )
            eid = cur.lastrowid
            # 同步失效覆盖
            conn.execute(
                "UPDATE overrides SET active=0 WHERE screen_id=? AND official=1",
                (screen_id,),
            )
            conn.commit()
        write_history("panic", eid, "official", reason, user["username"])
        write_audit(user["username"], "panic.official", {"id": eid, "screen_id": screen_id})
        return {"id": eid, "path": "official"}
    finally:
        release(lock_key, user["username"])


@router.post("/shadow")
def panic_shadow(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    screen_id = require_positive_int(body.get("screen_id"), "屏幕编号")
    reason = require_title(body.get("reason") or "影子撤屏草案", "原因")
    with connect() as conn:
        screen = conn.execute("SELECT * FROM screens WHERE id=?", (screen_id,)).fetchone()
        if not screen:
            raise HTTPException(404, "屏幕不存在")
        cur = conn.execute(
            "INSERT INTO panic_shadows(screen_id,reason,status,created_at,created_by) VALUES(?,?,?,?,?)",
            (screen_id, reason, "open", time.time(), user["username"]),
        )
        sid = cur.lastrowid
        conn.commit()
    write_history("panic_shadow", sid, "create", reason, user["username"])
    return {"id": sid, "path": "shadow"}


@router.post("/shadow/{shadow_id}/promote")
def promote_panic(shadow_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        sh = conn.execute("SELECT * FROM panic_shadows WHERE id=?", (shadow_id,)).fetchone()
        if not sh or sh["status"] != "open":
            raise HTTPException(409, "影子不可升正")
        screen_id = sh["screen_id"]
        reason = sh["reason"]
    lock_key = _acquire_publish_lock(screen_id, user, f"升正撤屏影子 {shadow_id}：{reason}")
    try:
        with connect() as conn:
            conn.execute("DELETE FROM publications WHERE screen_id=? AND official=1", (screen_id,))
            cur = conn.execute(
                "INSERT INTO panic_events(screen_id,reason,official,created_at,created_by) VALUES(?,?,?,?,?)",
                (screen_id, reason, 1, time.time(), user["username"]),
            )
            eid = cur.lastrowid
            conn.execute("UPDATE panic_shadows SET status='promoted' WHERE id=?", (shadow_id,))
            conn.execute(
                "UPDATE overrides SET active=0 WHERE screen_id=? AND official=1",
                (screen_id,),
            )
            conn.commit()
        write_history("panic", eid, "promote_shadow", reason, user["username"])
        return {"id": eid, "path": "shadow_promote"}
    finally:
        release(lock_key, user["username"])
