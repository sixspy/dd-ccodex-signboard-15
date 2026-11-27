"""领域常量与产品元数据。"""
from __future__ import annotations

PRODUCT_NAME = "楼宇数字标牌编排"
SKELETON = "楼宇屏幕按清单与时段窗编排内容，发布须版本落库才能上屏，紧急撤屏与变更历史同源。"
DOMAIN = "应用开发"
SUB_DIRECTION = "全栈开发"

USERS = {
    "admin": {"password": "admin123", "role": "admin", "display": "平台管理员"},
    "writer": {"password": "writer123", "role": "writer", "display": "编排员"},
    "viewer": {"password": "viewer123", "role": "viewer", "display": "观察员"},
}

ASSET_KINDS = ("image", "video", "html", "ticker")
ASSET_STATUS = ("draft", "ready", "retired")
SCREEN_STATUS = ("online", "offline", "maintenance")
PLAYLIST_STATUS = ("draft", "ready", "archived")
WINDOW_STATUS = ("open", "closed", "paused")
PUBLISH_STATUS = ("draft", "published", "rolled_back")
SHADOW_STATUS = ("open", "promoted", "discarded")
OVERRIDE_EFFECT = ("force_playlist", "force_blank", "force_asset")
ZONE_TYPES = ("lobby", "elevator", "corridor", "meeting", "outdoor")

ASSET_KIND_LABEL = {
    "image": "图片",
    "video": "视频",
    "html": "网页页",
    "ticker": "滚动条",
}
ASSET_STATUS_LABEL = {
    "draft": "草稿",
    "ready": "可播",
    "retired": "已退役",
}
SCREEN_STATUS_LABEL = {
    "online": "在线",
    "offline": "离线",
    "maintenance": "维保",
}
PUBLISH_STATUS_LABEL = {
    "draft": "草稿",
    "published": "已上屏",
    "rolled_back": "已回退",
}
SHADOW_STATUS_LABEL = {
    "open": "待升正",
    "promoted": "已升正",
    "discarded": "已废弃",
}
OVERRIDE_EFFECT_LABEL = {
    "force_playlist": "强制清单",
    "force_blank": "强制空屏",
    "force_asset": "强制单素材",
}
ZONE_TYPE_LABEL = {
    "lobby": "大堂",
    "elevator": "电梯厅",
    "corridor": "走廊",
    "meeting": "会议室",
    "outdoor": "室外",
}

# 业务说明块：给编排员与题面空桩对齐的领域词典（须保持可读，禁止无调用死代码）。
DOMAIN_GLOSSARY = {
    "asset": "可上屏素材条目，含种类、时长、分辨率约束",
    "screen": "物理或虚拟终端屏幕，绑定楼层与分区",
    "zone": "楼宇分区，约束可播清单与风险等级",
    "playlist": "有序素材序列，含循环与过渡",
    "window": "时段窗，限制清单在哪些钟点可播",
    "publish": "将清单与时段窗绑定到屏幕并升版本",
    "panic": "紧急撤屏，清空正式播放配置",
    "override": "单屏临时覆盖，优先于正式发布",
    "layout": "屏幕布局槽位，决定多区画布",
    "evaluate": "给定时刻求某屏应播内容",
}

RISK_LEVELS = {
    1: "低风险演示区",
    2: "一般办公区",
    3: "客户可见区",
    4: "室外高曝光",
    5: "政务敏感区",
}

DEFAULT_DURATIONS = {
    "image": 12,
    "video": 30,
    "html": 20,
    "ticker": 8,
}

RESOLUTION_PRESETS = (
    ("1920x1080", "横屏全高清"),
    ("1080x1920", "竖屏全高清"),
    ("3840x2160", "横屏超高清"),
    ("1280x720", "横屏高清"),
)

TRANSITION_KINDS = ("cut", "fade", "slide_left", "slide_up")
TRANSITION_LABEL = {
    "cut": "硬切",
    "fade": "淡入淡出",
    "slide_left": "左滑",
    "slide_up": "上滑",
}
