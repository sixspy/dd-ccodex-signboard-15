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
