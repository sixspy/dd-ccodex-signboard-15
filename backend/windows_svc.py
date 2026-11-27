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
