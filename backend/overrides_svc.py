"""单屏覆盖。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from locks import acquire, release
from policies import assert_override_payload
from validators import require_effect, require_positive_int

router = APIRouter(prefix="/api/overrides", tags=["overrides"])


@router.get("")
def list_overrides(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(
            conn.execute(
                """
                SELECT o.*, s.code screen_code
                FROM overrides o JOIN screens s ON s.id=o.screen_id
                WHERE o.official=1
                ORDER BY o.id DESC
                """
            ).fetchall()
        )
    return {"items": rows}


@router.get("/shadows")
def list_shadows(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(conn.execute("SELECT * FROM override_shadows ORDER BY id DESC").fetchall())
    return {"items": rows}


@router.post("/official")
def override_official(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    screen_id = require_positive_int(body.get("screen_id"), "屏幕编号")
    effect = require_effect(body.get("effect"))
    playlist_id = body.get("playlist_id")
    asset_id = body.get("asset_id")
    assert_override_payload(effect, playlist_id, asset_id)
    lock_key = f"override:{screen_id}"
    acquire(lock_key, user["username"])
    try:
        with connect() as conn:
            if not conn.execute("SELECT id FROM screens WHERE id=?", (screen_id,)).fetchone():
                raise HTTPException(404, "屏幕不存在")
            conn.execute(
                "UPDATE overrides SET active=0 WHERE screen_id=? AND official=1",
                (screen_id,),
            )
            cur = conn.execute(
                "INSERT INTO overrides(screen_id,effect,playlist_id,asset_id,note,official,active,created_at,created_by) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    screen_id,
                    effect,
                    playlist_id,
                    asset_id,
                    body.get("note") or "",
                    1,
                    1,
                    time.time(),
                    user["username"],
                ),
            )
            oid = cur.lastrowid
            conn.commit()
        write_history("override", oid, "official", effect, user["username"])
        write_audit(user["username"], "override.official", {"id": oid})
        return {"id": oid, "path": "official"}
    finally:
        release(lock_key, user["username"])


@router.post("/shadow")
def override_shadow(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    screen_id = require_positive_int(body.get("screen_id"), "屏幕编号")
    effect = require_effect(body.get("effect"))
    playlist_id = body.get("playlist_id")
    asset_id = body.get("asset_id")
    assert_override_payload(effect, playlist_id, asset_id)
    with connect() as conn:
        if not conn.execute("SELECT id FROM screens WHERE id=?", (screen_id,)).fetchone():
            raise HTTPException(404, "屏幕不存在")
        cur = conn.execute(
            "INSERT INTO override_shadows(screen_id,effect,playlist_id,asset_id,note,status,created_at,created_by) VALUES(?,?,?,?,?,?,?,?)",
            (
                screen_id,
                effect,
                playlist_id,
                asset_id,
                body.get("note") or "",
                "open",
                time.time(),
                user["username"],
            ),
        )
        sid = cur.lastrowid
        conn.commit()
    return {"id": sid, "path": "shadow"}


@router.post("/shadow/{shadow_id}/promote")
def promote_override(shadow_id: int, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        sh = conn.execute("SELECT * FROM override_shadows WHERE id=?", (shadow_id,)).fetchone()
        if not sh or sh["status"] != "open":
            raise HTTPException(409, "影子不可升正")
        screen_id = sh["screen_id"]
    lock_key = f"override:{screen_id}"
    acquire(lock_key, user["username"])
    try:
        with connect() as conn:
            sh = conn.execute("SELECT * FROM override_shadows WHERE id=?", (shadow_id,)).fetchone()
            conn.execute(
                "UPDATE overrides SET active=0 WHERE screen_id=? AND official=1",
                (screen_id,),
            )
            cur = conn.execute(
                "INSERT INTO overrides(screen_id,effect,playlist_id,asset_id,note,official,active,created_at,created_by) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    sh["screen_id"],
                    sh["effect"],
                    sh["playlist_id"],
                    sh["asset_id"],
                    sh["note"],
                    1,
                    1,
                    time.time(),
                    user["username"],
                ),
            )
            oid = cur.lastrowid
            conn.execute("UPDATE override_shadows SET status='promoted' WHERE id=?", (shadow_id,))
            conn.commit()
        write_history("override", oid, "promote_shadow", sh["effect"], user["username"])
        return {"id": oid, "path": "shadow_promote"}
    finally:
        release(lock_key, user["username"])
