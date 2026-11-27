"""发布上屏（正式事务 vs 影子升正 空桩可扩展）。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_contention, write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from locks import LockBusy, acquire, release
from policies import assert_playlist_ready, assert_screen_online, assert_window_open
from validators import require_positive_int, require_title

router = APIRouter(prefix="/api/publish", tags=["publish"])


@router.get("/official")
def list_official(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(
            conn.execute(
                """
                SELECT p.*, s.code screen_code, s.title screen_title,
                       pl.code playlist_code, w.code window_code
                FROM publications p
                JOIN screens s ON s.id=p.screen_id
                JOIN playlists pl ON pl.id=p.playlist_id
                JOIN time_windows w ON w.id=p.window_id
                WHERE p.official=1
                ORDER BY p.id DESC
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
                SELECT sh.*, s.code screen_code, pl.code playlist_code, w.code window_code
                FROM publish_shadows sh
                JOIN screens s ON s.id=sh.screen_id
                JOIN playlists pl ON pl.id=sh.playlist_id
                JOIN time_windows w ON w.id=sh.window_id
                ORDER BY sh.id DESC
                """
            ).fetchall()
        )
    return {"items": rows}


def _load_refs(conn, screen_id, playlist_id, window_id):
    screen = conn.execute("SELECT * FROM screens WHERE id=?", (screen_id,)).fetchone()
    playlist = conn.execute("SELECT * FROM playlists WHERE id=?", (playlist_id,)).fetchone()
    window = conn.execute("SELECT * FROM time_windows WHERE id=?", (window_id,)).fetchone()
    if not screen or not playlist or not window:
        raise HTTPException(404, "屏幕/清单/时段窗不存在")
    assert_screen_online(screen["status"])
    assert_playlist_ready(playlist["status"])
    assert_window_open(window["status"])
    return screen, playlist, window


def _acquire_publish_lock(screen_id: int, user: dict, summary: str) -> None:
    """同屏正式发布互斥闸口：争用败方整笔拒写，只留争用痕（正式区零改）。"""
    lock_key = f"publish:{screen_id}"
    try:
        acquire(lock_key, user["username"])
    except LockBusy as exc:
        write_contention(
            "publish",
            screen_id,
            user["username"],
            f"同屏正式发布争用败方，整笔拒写：{summary}",
            {"lock_key": lock_key, "winner": exc.holder},
        )
        raise HTTPException(
            409,
            f"同屏正式发布争用：{exc.holder} 持锁在途，本笔整笔拒写且正式区零改",
        ) from exc


def _assert_single_official(conn, screen_id: int) -> None:
    """事务内联查跨表账实：同屏正式发布恒唯一，双行即数据事故必须显式报错。"""
    n = conn.execute(
        "SELECT COUNT(*) c FROM publications WHERE screen_id=? AND official=1",
        (screen_id,),
    ).fetchone()["c"]
    if n > 1:
        raise HTTPException(500, f"正式发布不唯一：屏幕{screen_id}存在{n}行正式发布，账实事故")


@router.post("/official")
def publish_official(body: dict, authorization: str | None = Header(default=None)):
    """甲路径：同事务写入正式发布并升版本。"""
    user = current_user(authorization)
    require_writer(user)
    screen_id = require_positive_int(body.get("screen_id"), "屏幕编号")
    playlist_id = require_positive_int(body.get("playlist_id"), "清单编号")
    window_id = require_positive_int(body.get("window_id"), "时段编号")
    summary = require_title(body.get("summary") or "正式发布", "发布摘要")
    layout_id = body.get("layout_id")
    lock_key = f"publish:{screen_id}"
    _acquire_publish_lock(screen_id, user, summary)
    try:
        with connect() as conn:
            _load_refs(conn, screen_id, playlist_id, window_id)
            prev = conn.execute(
                "SELECT version FROM publications WHERE screen_id=? AND official=1",
                (screen_id,),
            ).fetchone()
            version = (prev["version"] + 1) if prev else 1
            conn.execute("DELETE FROM publications WHERE screen_id=? AND official=1", (screen_id,))
            cur = conn.execute(
                "INSERT INTO publications(screen_id,playlist_id,window_id,layout_id,version,summary,status,official,published_at,published_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    screen_id,
                    playlist_id,
                    window_id,
                    layout_id,
                    version,
                    summary,
                    "published",
                    1,
                    time.time(),
                    user["username"],
                ),
            )
            pid = cur.lastrowid
            _assert_single_official(conn, screen_id)
            conn.commit()
        write_history("publication", pid, "publish_official", summary, user["username"])
        write_audit(user["username"], "publish.official", {"id": pid, "version": version})
        return {"id": pid, "version": version, "path": "official"}
    finally:
        release(lock_key, user["username"])


@router.post("/shadow")
def create_shadow(body: dict, authorization: str | None = Header(default=None)):
    """乙路径第一步：只写影子草案，正式区零改。"""
    user = current_user(authorization)
    require_writer(user)
    screen_id = require_positive_int(body.get("screen_id"), "屏幕编号")
    playlist_id = require_positive_int(body.get("playlist_id"), "清单编号")
    window_id = require_positive_int(body.get("window_id"), "时段编号")
    summary = require_title(body.get("summary") or "影子发布草案", "发布摘要")
    layout_id = body.get("layout_id")
    with connect() as conn:
        _load_refs(conn, screen_id, playlist_id, window_id)
        cur = conn.execute(
            "INSERT INTO publish_shadows(screen_id,playlist_id,window_id,layout_id,summary,status,created_at,created_by) VALUES(?,?,?,?,?,?,?,?)",
            (
                screen_id,
                playlist_id,
                window_id,
                layout_id,
                summary,
                "open",
                time.time(),
                user["username"],
            ),
        )
        sid = cur.lastrowid
        conn.commit()
    write_history("publish_shadow", sid, "create", summary, user["username"])
    return {"id": sid, "path": "shadow", "status": "open"}


@router.post("/shadow/{shadow_id}/promote")
def promote_shadow(shadow_id: int, authorization: str | None = Header(default=None)):
    """乙路径升正：原子落正式区。"""
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        sh = conn.execute("SELECT * FROM publish_shadows WHERE id=?", (shadow_id,)).fetchone()
        if not sh:
            raise HTTPException(404, "影子不存在")
        if sh["status"] != "open":
            raise HTTPException(409, "影子不可升正")
        screen_id = sh["screen_id"]
        promote_summary = f"升正影子 {shadow_id}：{sh['summary']}"
    lock_key = f"publish:{screen_id}"
    try:
        acquire(lock_key, user["username"])
    except LockBusy as exc:
        write_contention(
            "publish",
            screen_id,
            user["username"],
            f"影子升正争用败方，整笔拒写：{promote_summary}",
            {"lock_key": lock_key, "winner": exc.holder, "shadow_id": shadow_id},
        )
        raise HTTPException(
            409,
            f"同屏正式发布争用：{exc.holder} 持锁在途，升正整笔拒写且正式区零改",
        ) from exc
    try:
        with connect() as conn:
            sh = conn.execute("SELECT * FROM publish_shadows WHERE id=?", (shadow_id,)).fetchone()
            _load_refs(conn, sh["screen_id"], sh["playlist_id"], sh["window_id"])
            prev = conn.execute(
                "SELECT version FROM publications WHERE screen_id=? AND official=1",
                (sh["screen_id"],),
            ).fetchone()
            version = (prev["version"] + 1) if prev else 1
            conn.execute("DELETE FROM publications WHERE screen_id=? AND official=1", (sh["screen_id"],))
            cur = conn.execute(
                "INSERT INTO publications(screen_id,playlist_id,window_id,layout_id,version,summary,status,official,published_at,published_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    sh["screen_id"],
                    sh["playlist_id"],
                    sh["window_id"],
                    sh["layout_id"],
                    version,
                    sh["summary"],
                    "published",
                    1,
                    time.time(),
                    user["username"],
                ),
            )
            pid = cur.lastrowid
            conn.execute(
                "UPDATE publish_shadows SET status='promoted' WHERE id=?",
                (shadow_id,),
            )
            _assert_single_official(conn, sh["screen_id"])
            conn.commit()
        write_history("publication", pid, "promote_shadow", f"升正影子 {shadow_id}", user["username"])
        write_audit(user["username"], "publish.promote", {"shadow_id": shadow_id, "id": pid})
        return {"id": pid, "version": version, "path": "shadow_promote"}
    finally:
        release(lock_key, user["username"])
