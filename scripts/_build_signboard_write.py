# -*- coding: utf-8 -*-
"""signboard 发布/撤屏/覆盖/求值等写路径服务。"""
from __future__ import annotations

PUBLISH = r'''
"""发布上屏（正式事务 vs 影子升正 空桩可扩展）。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from locks import acquire, release
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
    acquire(lock_key, user["username"])
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
    lock_key = f"publish:{screen_id}"
    acquire(lock_key, user["username"])
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
            conn.commit()
        write_history("publication", pid, "promote_shadow", f"升正影子 {shadow_id}", user["username"])
        write_audit(user["username"], "publish.promote", {"shadow_id": shadow_id, "id": pid})
        return {"id": pid, "version": version, "path": "shadow_promote"}
    finally:
        release(lock_key, user["username"])
'''

PANIC = r'''
"""紧急撤屏。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from locks import acquire, release
from validators import require_positive_int, require_title

router = APIRouter(prefix="/api/panic", tags=["panic"])


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
    lock_key = f"publish:{screen_id}"
    acquire(lock_key, user["username"])
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
    lock_key = f"publish:{screen_id}"
    acquire(lock_key, user["username"])
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
'''

OVERRIDES = r'''
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
'''

EVALUATE = r'''
"""在线求值：某屏此刻应播什么。"""
from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, Header, HTTPException

from auth import current_user
from db import connect, rows_to_list
from validators import require_hm, require_positive_int, window_covers

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])


@router.post("/screen")
def evaluate_screen(body: dict, authorization: str | None = Header(default=None)):
    current_user(authorization)
    screen_id = require_positive_int(body.get("screen_id"), "屏幕编号")
    now_hm = require_hm(body.get("now_hm") or datetime.now().strftime("%H:%M"), "求值时刻")
    weekday = str(body.get("weekday") or datetime.now().isoweekday())
    with connect() as conn:
        screen = conn.execute("SELECT * FROM screens WHERE id=?", (screen_id,)).fetchone()
        if not screen:
            raise HTTPException(404, "屏幕不存在")
        ov = conn.execute(
            "SELECT * FROM overrides WHERE screen_id=? AND official=1 AND active=1 ORDER BY id DESC LIMIT 1",
            (screen_id,),
        ).fetchone()
        if ov:
            result = {
                "source": "override",
                "effect": ov["effect"],
                "playlist_id": ov["playlist_id"],
                "asset_id": ov["asset_id"],
                "now_hm": now_hm,
            }
            if ov["effect"] == "force_blank":
                result["play"] = None
            elif ov["effect"] == "force_asset" and ov["asset_id"]:
                asset = conn.execute("SELECT * FROM assets WHERE id=?", (ov["asset_id"],)).fetchone()
                result["play"] = {"kind": "asset", "asset": dict(asset) if asset else None}
            elif ov["effect"] == "force_playlist" and ov["playlist_id"]:
                items = rows_to_list(
                    conn.execute(
                        "SELECT * FROM playlist_items WHERE playlist_id=? ORDER BY seq",
                        (ov["playlist_id"],),
                    ).fetchall()
                )
                result["play"] = {"kind": "playlist", "items": items}
            return result
        pub = conn.execute(
            "SELECT * FROM publications WHERE screen_id=? AND official=1 AND status='published'",
            (screen_id,),
        ).fetchone()
        if not pub:
            return {"source": "empty", "play": None, "now_hm": now_hm, "reason": "无正式发布"}
        window = conn.execute(
            "SELECT * FROM time_windows WHERE id=?",
            (pub["window_id"],),
        ).fetchone()
        if weekday not in set((window["weekdays"] or "").split(",")):
            return {"source": "publication", "play": None, "reason": "非开放星期", "now_hm": now_hm}
        if not window_covers(window["start_hm"], window["end_hm"], now_hm):
            return {"source": "publication", "play": None, "reason": "不在时段窗内", "now_hm": now_hm}
        items = rows_to_list(
            conn.execute(
                """
                SELECT i.*, a.code asset_code, a.title asset_title, a.kind
                FROM playlist_items i JOIN assets a ON a.id=i.asset_id
                WHERE i.playlist_id=? ORDER BY i.seq
                """,
                (pub["playlist_id"],),
            ).fetchall()
        )
        return {
            "source": "publication",
            "version": pub["version"],
            "playlist_id": pub["playlist_id"],
            "window_id": pub["window_id"],
            "play": {"kind": "playlist", "items": items},
            "now_hm": now_hm,
        }
'''

HISTORY = r'''
"""变更历史。"""
from __future__ import annotations

from fastapi import APIRouter, Header

from auth import current_user
from db import connect, rows_to_list

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def list_history(limit: int = 100, authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(
            conn.execute(
                "SELECT * FROM change_history ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 300)),),
            ).fetchall()
        )
    return {"items": rows}
'''

LAYOUTS = r'''
"""屏幕布局槽位。"""
from __future__ import annotations

import json
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from validators import require_code, require_title

router = APIRouter(prefix="/api/layouts", tags=["layouts"])


@router.get("")
def list_layouts(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(conn.execute("SELECT * FROM layouts ORDER BY id").fetchall())
    for r in rows:
        try:
            r["slots"] = json.loads(r["slots_json"])
        except json.JSONDecodeError:
            r["slots"] = []
    return {"items": rows}


@router.post("")
def create_layout(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    code = require_code(body.get("code"), "布局编码")
    title = require_title(body.get("title"), "布局标题")
    slots = body.get("slots") or []
    if not isinstance(slots, list) or not slots:
        raise HTTPException(400, "布局至少包含一个槽位")
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO layouts(code,title,slots_json,note) VALUES(?,?,?,?)",
                (code, title, json.dumps(slots, ensure_ascii=False), body.get("note") or ""),
            )
            lid = cur.lastrowid
            conn.commit()
        except Exception as exc:
            raise HTTPException(409, f"布局编码冲突: {exc}") from exc
    write_history("layout", lid, "create", f"创建布局 {code}", user["username"])
    return {"id": lid, "code": code}
'''

STUBS = r'''
"""具名空桩：题面可点名，固定 501。"""
from __future__ import annotations

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

from auth import current_user

router = APIRouter(prefix="/api/stubs", tags=["stubs"])

STUB_META = {
    "remote_push": {
        "title": "远程推屏桥",
        "desc": "将正式发布推送到边缘播放器集群（空桩）",
    },
    "media_bridge": {
        "title": "媒资中台桥接",
        "desc": "从媒资中台同步素材元数据（空桩）",
    },
}


@router.get("")
def list_stubs(authorization: str | None = Header(default=None)):
    current_user(authorization)
    return {"items": [{"key": k, **v, "status": "not_implemented"} for k, v in STUB_META.items()]}


@router.post("/remote_push")
def remote_push(body: dict, authorization: str | None = Header(default=None)):
    current_user(authorization)
    return JSONResponse(
        status_code=501,
        content={"ok": False, "stub": "remote_push", "detail": "远程推屏桥尚未实现", "body": body},
    )


@router.post("/media_bridge")
def media_bridge(body: dict, authorization: str | None = Header(default=None)):
    current_user(authorization)
    return JSONResponse(
        status_code=501,
        content={"ok": False, "stub": "media_bridge", "detail": "媒资中台桥接尚未实现", "body": body},
    )
'''

APP = r'''
"""楼宇数字标牌编排 — FastAPI 入口。"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from assets_svc import router as assets_router
from audit_svc import router as audit_router
from auth import router as auth_router
from dashboard_svc import router as dashboard_router
from db import FRONTEND, PRODUCT_META, init_db
from evaluate_svc import router as evaluate_router
from history_svc import router as history_router
from layouts_svc import router as layouts_router
from locks import router as locks_router
from overrides_svc import router as overrides_router
from panic_svc import router as panic_router
from playlists_svc import router as playlists_router
from publish_svc import router as publish_router
from screens_svc import router as screens_router
from stubs_svc import router as stubs_router
from windows_svc import router as windows_router
from zones_svc import router as zones_router

PRODUCT = PRODUCT_META["name"]
SKELETON = PRODUCT_META["skeleton"]

app = FastAPI(title=PRODUCT, description=SKELETON)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    auth_router,
    dashboard_router,
    zones_router,
    screens_router,
    assets_router,
    layouts_router,
    playlists_router,
    windows_router,
    publish_router,
    panic_router,
    overrides_router,
    evaluate_router,
    history_router,
    locks_router,
    audit_router,
    stubs_router,
):
    app.include_router(r)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    from db import DB_PATH, connect

    with connect() as conn:
        screens = conn.execute("SELECT COUNT(*) c FROM screens").fetchone()["c"]
        pubs = conn.execute(
            "SELECT COUNT(*) c FROM publications WHERE official=1 AND status='published'"
        ).fetchone()["c"]
        tables = conn.execute(
            "SELECT COUNT(*) c FROM sqlite_master WHERE type='table'"
        ).fetchone()["c"]
    return {
        "ok": True,
        "product": PRODUCT,
        "domain": PRODUCT_META["domain"],
        "sub_direction": PRODUCT_META["sub"],
        "skeleton": SKELETON,
        "screens": screens,
        "official_publications": pubs,
        "tables": tables,
        "db": str(DB_PATH),
    }


app.mount("/assets", StaticFiles(directory=str(FRONTEND)), name="assets")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
'''
