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
