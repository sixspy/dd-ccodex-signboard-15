# -*- coding: utf-8 -*-
"""signboard 主业务服务常量。"""
from __future__ import annotations

DASHBOARD = r'''
"""总览。"""
from __future__ import annotations

from fastapi import APIRouter, Header

from auth import current_user
from db import PRODUCT_META, connect

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        screens = conn.execute("SELECT COUNT(*) c FROM screens").fetchone()["c"]
        online = conn.execute("SELECT COUNT(*) c FROM screens WHERE status='online'").fetchone()["c"]
        assets = conn.execute("SELECT COUNT(*) c FROM assets WHERE status='ready'").fetchone()["c"]
        pubs = conn.execute(
            "SELECT COUNT(*) c FROM publications WHERE official=1 AND status='published'"
        ).fetchone()["c"]
        shadows = conn.execute(
            "SELECT COUNT(*) c FROM publish_shadows WHERE status='open'"
        ).fetchone()["c"]
        panics = conn.execute("SELECT COUNT(*) c FROM panic_events").fetchone()["c"]
        overrides = conn.execute(
            "SELECT COUNT(*) c FROM overrides WHERE official=1 AND active=1"
        ).fetchone()["c"]
    return {
        "product": PRODUCT_META["name"],
        "domain": PRODUCT_META["domain"],
        "sub": PRODUCT_META["sub"],
        "skeleton": PRODUCT_META["skeleton"],
        "screens": screens,
        "online_screens": online,
        "ready_assets": assets,
        "official_publications": pubs,
        "open_shadows": shadows,
        "panic_events": panics,
        "active_overrides": overrides,
    }
'''

ASSETS = r'''
"""素材台账。"""
from __future__ import annotations

import time
from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect, row_to_dict, rows_to_list
from models import ASSET_KIND_LABEL, ASSET_STATUS_LABEL, DEFAULT_DURATIONS
from validators import require_asset_status, require_code, require_kind, require_positive_int, require_title

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _enrich(row: dict) -> dict:
    row["kind_label"] = ASSET_KIND_LABEL.get(row["kind"], row["kind"])
    row["status_label"] = ASSET_STATUS_LABEL.get(row["status"], row["status"])
    return row


@router.get("")
def list_assets(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(conn.execute("SELECT * FROM assets ORDER BY id DESC").fetchall())
    return {"items": [_enrich(r) for r in rows]}


@router.get("/{asset_id}")
def get_asset(asset_id: int, authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
    if not row:
        raise HTTPException(404, "素材不存在")
    return _enrich(dict(row))


@router.post("")
def create_asset(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    code = require_code(body.get("code"), "素材编码")
    title = require_title(body.get("title"), "素材标题")
    kind = require_kind(body.get("kind"))
    duration = require_positive_int(
        body.get("duration_sec", DEFAULT_DURATIONS.get(kind, 10)), "时长", 1, 3600
    )
    resolution = (body.get("resolution") or "1920x1080").strip()
    status = require_asset_status(body.get("status") or "draft")
    checksum = (body.get("checksum") or "").strip()
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO assets(code,title,kind,duration_sec,resolution,status,owner,created_at,checksum) VALUES(?,?,?,?,?,?,?,?,?)",
                (code, title, kind, duration, resolution, status, user["username"], time.time(), checksum),
            )
            aid = cur.lastrowid
            conn.commit()
        except Exception as exc:
            raise HTTPException(409, f"素材编码冲突: {exc}") from exc
    write_history("asset", aid, "create", f"创建素材 {code}", user["username"])
    write_audit(user["username"], "asset.create", {"id": aid, "code": code})
    return {"id": aid, "code": code}


@router.patch("/{asset_id}")
def patch_asset(asset_id: int, body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id=?", (asset_id,)).fetchone()
        if not row:
            raise HTTPException(404, "素材不存在")
        title = require_title(body.get("title", row["title"]), "素材标题")
        status = require_asset_status(body.get("status", row["status"]))
        duration = require_positive_int(body.get("duration_sec", row["duration_sec"]), "时长", 1, 3600)
        conn.execute(
            "UPDATE assets SET title=?, status=?, duration_sec=? WHERE id=?",
            (title, status, duration, asset_id),
        )
        conn.commit()
    write_history("asset", asset_id, "patch", f"更新素材状态={status}", user["username"])
    return {"ok": True}
'''

SCREENS = r'''
"""屏幕台账。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_audit, write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from models import SCREEN_STATUS_LABEL, ZONE_TYPE_LABEL
from validators import require_code, require_screen_status, require_title

router = APIRouter(prefix="/api/screens", tags=["screens"])


def _enrich(row: dict, zone: dict | None = None) -> dict:
    row["status_label"] = SCREEN_STATUS_LABEL.get(row["status"], row["status"])
    if zone:
        row["zone_code"] = zone["code"]
        row["zone_title"] = zone["title"]
        row["zone_type_label"] = ZONE_TYPE_LABEL.get(zone["zone_type"], zone["zone_type"])
        row["risk_level"] = zone["risk_level"]
    return row


@router.get("")
def list_screens(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT s.*, z.code zone_code, z.title zone_title, z.zone_type, z.risk_level
            FROM screens s JOIN zones z ON z.id=s.zone_id
            ORDER BY s.id
            """
        ).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        d["status_label"] = SCREEN_STATUS_LABEL.get(d["status"], d["status"])
        d["zone_type_label"] = ZONE_TYPE_LABEL.get(d["zone_type"], d["zone_type"])
        items.append(d)
    return {"items": items}


@router.post("")
def create_screen(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    code = require_code(body.get("code"), "屏幕编码")
    title = require_title(body.get("title"), "屏幕标题")
    status = require_screen_status(body.get("status") or "offline")
    resolution = (body.get("resolution") or "1920x1080").strip()
    orientation = body.get("orientation") or "landscape"
    zone_code = (body.get("zone_code") or "").strip()
    with connect() as conn:
        zone = conn.execute("SELECT * FROM zones WHERE code=?", (zone_code,)).fetchone()
        if not zone:
            raise HTTPException(404, "分区不存在")
        try:
            cur = conn.execute(
                "INSERT INTO screens(code,title,zone_id,resolution,status,orientation,note) VALUES(?,?,?,?,?,?,?)",
                (code, title, zone["id"], resolution, status, orientation, body.get("note") or ""),
            )
            sid = cur.lastrowid
            conn.commit()
        except Exception as exc:
            raise HTTPException(409, f"屏幕编码冲突: {exc}") from exc
    write_history("screen", sid, "create", f"登记屏幕 {code}", user["username"])
    write_audit(user["username"], "screen.create", {"id": sid, "code": code})
    return {"id": sid, "code": code}


@router.patch("/{screen_id}")
def patch_screen(screen_id: int, body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM screens WHERE id=?", (screen_id,)).fetchone()
        if not row:
            raise HTTPException(404, "屏幕不存在")
        status = require_screen_status(body.get("status", row["status"]))
        title = require_title(body.get("title", row["title"]), "屏幕标题")
        note = body.get("note", row["note"])
        conn.execute(
            "UPDATE screens SET title=?, status=?, note=? WHERE id=?",
            (title, status, note, screen_id),
        )
        conn.commit()
    write_history("screen", screen_id, "patch", f"屏幕状态={status}", user["username"])
    return {"ok": True}
'''

ZONES = r'''
"""楼宇分区。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from models import RISK_LEVELS, ZONE_TYPE_LABEL
from policies import assert_zone_risk_for_outdoor
from validators import require_code, require_positive_int, require_title, require_zone_type

router = APIRouter(prefix="/api/zones", tags=["zones"])


@router.get("")
def list_zones(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(conn.execute("SELECT * FROM zones ORDER BY id").fetchall())
    for r in rows:
        r["zone_type_label"] = ZONE_TYPE_LABEL.get(r["zone_type"], r["zone_type"])
        r["risk_label"] = RISK_LEVELS.get(r["risk_level"], str(r["risk_level"]))
    return {"items": rows}


@router.post("")
def create_zone(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    code = require_code(body.get("code"), "分区编码")
    title = require_title(body.get("title"), "分区标题")
    zone_type = require_zone_type(body.get("zone_type"))
    risk = require_positive_int(body.get("risk_level", 2), "风险等级", 1, 5)
    assert_zone_risk_for_outdoor(zone_type, risk)
    floor_label = (body.get("floor_label") or "").strip()
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO zones(code,title,zone_type,risk_level,floor_label) VALUES(?,?,?,?,?)",
                (code, title, zone_type, risk, floor_label),
            )
            zid = cur.lastrowid
            conn.commit()
        except Exception as exc:
            raise HTTPException(409, f"分区编码冲突: {exc}") from exc
    write_history("zone", zid, "create", f"创建分区 {code}", user["username"])
    return {"id": zid, "code": code}
'''

PLAYLISTS = r'''
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
'''

WINDOWS = r'''
"""时段窗。"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from audit_svc import write_history
from auth import current_user, require_writer
from db import connect, rows_to_list
from validators import (
    hm_to_min,
    require_code,
    require_hm,
    require_title,
    require_weekdays,
    require_window_status,
)

router = APIRouter(prefix="/api/windows", tags=["windows"])


@router.get("")
def list_windows(authorization: str | None = Header(default=None)):
    current_user(authorization)
    with connect() as conn:
        rows = rows_to_list(conn.execute("SELECT * FROM time_windows ORDER BY id").fetchall())
    for r in rows:
        r["span_min"] = (hm_to_min(r["end_hm"]) - hm_to_min(r["start_hm"])) % (24 * 60)
    return {"items": rows}


@router.post("")
def create_window(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    code = require_code(body.get("code"), "时段编码")
    title = require_title(body.get("title"), "时段标题")
    start_hm = require_hm(body.get("start_hm"), "开始时刻")
    end_hm = require_hm(body.get("end_hm"), "结束时刻")
    weekdays = require_weekdays(body.get("weekdays") or "1,2,3,4,5")
    status = require_window_status(body.get("status") or "open")
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO time_windows(code,title,start_hm,end_hm,weekdays,status,note) VALUES(?,?,?,?,?,?,?)",
                (code, title, start_hm, end_hm, weekdays, status, body.get("note") or ""),
            )
            wid = cur.lastrowid
            conn.commit()
        except Exception as exc:
            raise HTTPException(409, f"时段编码冲突: {exc}") from exc
    write_history("window", wid, "create", f"创建时段窗 {code}", user["username"])
    return {"id": wid, "code": code}


@router.patch("/{window_id}")
def patch_window(window_id: int, body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    with connect() as conn:
        row = conn.execute("SELECT * FROM time_windows WHERE id=?", (window_id,)).fetchone()
        if not row:
            raise HTTPException(404, "时段窗不存在")
        status = require_window_status(body.get("status", row["status"]))
        title = require_title(body.get("title", row["title"]), "时段标题")
        conn.execute(
            "UPDATE time_windows SET title=?, status=? WHERE id=?",
            (title, status, window_id),
        )
        conn.commit()
    write_history("window", window_id, "patch", f"时段状态={status}", user["username"])
    return {"ok": True}
'''
