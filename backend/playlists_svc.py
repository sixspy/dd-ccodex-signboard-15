"""播放清单。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from policies import assert_asset_ready, assert_resolution_compatible
from validators import require_code, require_playlist_status, require_positive_int, require_title, require_transition

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.get("")
def list_playlists(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(conn.execute("SELECT * FROM playlists ORDER BY id DESC").fetchall())
        for r in rows:
            r["item_count"] = conn.execute(
                "SELECT COUNT(*) c FROM playlist_items WHERE playlist_id=?",
                (r["id"],),
            ).fetchone()["c"]
    return {"items": rows}


@router.get("/{playlist_id}")
def get_playlist(playlist_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        pl = conn.execute("SELECT * FROM playlists WHERE id=?", (playlist_id,)).fetchone()
        if not pl:
            raise HTTPException(404, "清单不存在")
        items = rows_to_list(
            conn.execute(
                """
                SELECT i.*, a.code asset_code, a.title asset_title, a.kind, a.resolution
                FROM playlist_items i JOIN assets a ON a.id=i.asset_id
                WHERE i.playlist_id=? ORDER BY i.seq
                """,
                (playlist_id,),
            ).fetchall()
        )
    return {"playlist": dict(pl), "items": items}


@router.post("")
def create_playlist(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    code = require_code(body.get("code"), "清单编码")
    title = require_title(body.get("title"), "清单标题")
    status = require_playlist_status(body.get("status") or "draft")
    transition = require_transition(body.get("transition") or "cut")
    loop_flag = 1 if body.get("loop", True) else 0
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO playlists(code,title,status,transition,loop_flag,owner,created_at) VALUES(?,?,?,?,?,?,?)",
                (code, title, status, transition, loop_flag, user["username"], time.time()),
            )
            pid = cur.lastrowid
            conn.commit()
        except Exception as exc:
            raise HTTPException(409, f"清单编码冲突: {exc}") from exc
    write_history("playlist", pid, "create", f"创建清单 {code}", user["username"])
    write_audit(user["username"], "playlist.create", {"id": pid})
    return {"id": pid, "code": code}


@router.post("/{playlist_id}/items")
def add_item(playlist_id: int, body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    asset_id = require_positive_int(body.get("asset_id"), "素材编号")
    seq = require_positive_int(body.get("seq"), "序号", 1, 999)
    dwell = require_positive_int(body.get("dwell_sec", 10), "停留秒", 1, 3600)
    with connect() as conn:
        pl = conn.execute("SELECT * FROM playlists WHERE id=?", (playlist_id,)).fetchone()
        if not pl:
            raise HTTPException(404, "清单不存在")
        asset = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
        if not asset:
            raise HTTPException(404, "素材不存在")
        assert_asset_ready(asset["status"])
        try:
            conn.execute(
                "INSERT INTO playlist_items(playlist_id,asset_id,seq,dwell_sec) VALUES(?,?,?,?)",
                (playlist_id, asset_id, seq, dwell),
            )
            conn.commit()
        except Exception as exc:
            raise HTTPException(409, f"序号冲突: {exc}") from exc
    write_history("playlist", playlist_id, "add_item", f"加入素材 {asset_id} seq={seq}", user["username"])
    return {"ok": True}


@router.patch("/{playlist_id}")
def patch_playlist(playlist_id: int, body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        pl = conn.execute("SELECT * FROM playlists WHERE id=?", (playlist_id,)).fetchone()
        if not pl:
            raise HTTPException(404, "清单不存在")
        status = require_playlist_status(body.get("status", pl["status"]))
        title = require_title(body.get("title", pl["title"]), "清单标题")
        transition = require_transition(body.get("transition", pl["transition"]))
        if status == "ready":
            cnt = conn.execute(
                "SELECT COUNT(*) c FROM playlist_items WHERE playlist_id=?",
                (playlist_id,),
            ).fetchone()["c"]
            if cnt < 1:
                raise HTTPException(409, "空清单不可置为可播")
        conn.execute(
            "UPDATE playlists SET title=?, status=?, transition=? WHERE id=?",
            (title, status, transition, playlist_id),
        )
        conn.commit()
    write_history("playlist", playlist_id, "patch", f"清单状态={status}", user["username"])
    return {"ok": True}
