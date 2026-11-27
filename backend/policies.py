"""写入策略与风险闸。"""
from __future__ import annotations

from fastapi import HTTPException


def assert_zone_risk_for_outdoor(zone_type: str, risk_level: int) -> None:
    if zone_type == "outdoor" and risk_level < 3:
        raise HTTPException(400, "室外分区风险等级至少为 3")


def assert_playlist_ready(status: str) -> None:
    if status != "ready":
        raise HTTPException(409, "仅可播清单可发布上屏")


def assert_window_open(status: str) -> None:
    if status != "open":
        raise HTTPException(409, "时段窗未开放，禁止发布")


def assert_screen_online(status: str) -> None:
    if status == "maintenance":
        raise HTTPException(409, "维保中的屏幕禁止发布")


def assert_asset_ready(status: str) -> None:
    if status != "ready":
        raise HTTPException(409, "仅可播素材可进入清单")


def assert_resolution_compatible(screen_res: str, asset_res: str) -> None:
    if screen_res != asset_res and not asset_res.startswith(screen_res.split("x")[0]):
        # 允许同宽不同高的宽松匹配；完全无关则拒绝
        sw = screen_res.split("x")[0]
        aw = asset_res.split("x")[0]
        if sw != aw:
            raise HTTPException(409, "素材分辨率与屏幕不兼容")


def assert_override_payload(effect: str, playlist_id, asset_id) -> None:
    if effect == "force_playlist" and not playlist_id:
        raise HTTPException(400, "强制清单须指定清单")
    if effect == "force_asset" and not asset_id:
        raise HTTPException(400, "强制单素材须指定素材")
    if effect == "force_blank" and (playlist_id or asset_id):
        raise HTTPException(400, "强制空屏不得附带清单或素材")


POLICY_NOTES = [
    "客户可见区发布须有变更历史可追溯",
    "紧急撤屏后正式发布版本不得静默回写",
    "单屏覆盖激活时求值优先覆盖条目",
    "影子草案升正前正式区零改",
    "维保屏幕只允许查看不可发布",
]
