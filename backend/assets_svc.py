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
