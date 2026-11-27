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
