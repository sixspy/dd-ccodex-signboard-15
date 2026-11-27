# -*- coding: utf-8 -*-
"""生成 18-signboard 母仓（应用开发·全栈）。运行一次即可落地。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def w(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip("\n") if text.startswith("\n") else text, encoding="utf-8")
    print("wrote", rel, len(text.splitlines()), "lines")


def main() -> None:
    w(
        "requirements.txt",
        "fastapi==0.115.6\nuvicorn[standard]==0.32.1\npytest==8.3.4\nhttpx==0.28.1\n",
    )
    w(
        "pytest.ini",
        "[pytest]\npythonpath = backend\ntestpaths = tests\n",
    )
    w(
        ".gitignore",
        "data/\n__pycache__/\n.pytest_cache/\n*.pyc\n.venv/\n",
    )
    w(
        "Dockerfile",
        """
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn -r requirements.txt
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY fixtures/ ./fixtures/
COPY tests/ ./tests/
COPY pytest.ini .
RUN mkdir -p /app/data
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
""",
    )
    w(
        "docker-compose.yml",
        """
name: signboard
services:
  app:
    build: .
    ports:
      - "11730:8000"
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"]
      interval: 5s
      timeout: 5s
      retries: 12
""",
    )
    w(
        "README.md",
        """
# 楼宇数字标牌编排（signboard）

**所属领域：应用开发 · 子方向：全栈开发**

全栈产品：素材入库 → 屏幕台账 → 播放清单 → 时段窗 → 发布上屏 → 紧急撤屏 → 单屏覆盖 → 变更历史 → 在线求值。

## 骨架一句话

楼宇屏幕按清单与时段窗编排内容，发布须版本落库才能上屏，紧急撤屏与变更历史同源。

## H3 切口候选（写路径互斥 · 须择一）

1. **发布上屏**：同事务写入正式播放配置并升版本锁旧版，或只写影子发布草案、升正时原子落正式区（正式区升正前零改）。
2. **紧急撤屏**：同事务立即写正式空屏并记变更，或影子撤屏草案确认后原子撤屏。
3. **单屏覆盖**：同事务写正式覆盖条目，或影子覆盖草案升正。

正确性口径只能走甲乙中的一种且两边不得混用。

## 一键起环境

```bash
docker compose up -d --build
```

浏览器：http://localhost:11730

- `admin` / `admin123`（管理员）
- `writer` / `writer123`（编排员）
- `viewer` / `viewer123`（只读）

## 本地开发

```powershell
cd projects/18-signboard
$env:PYTHONPATH="backend"
python -m uvicorn app:app --app-dir backend --reload --port 8030
python -m pytest
python scripts/count_loc.py
```

## 空桩

- 远程推屏桥（`remote_push`）
- 媒资中台桥接（`media_bridge`）

接口固定返回 501，题面可点名。
""",
    )

    w("scripts/count_loc.py", COUNT_LOC)
    w("backend/__init__.py", '"""signboard backend."""\n')
    w("backend/models.py", MODELS)
    w("backend/db.py", DB)
    w("backend/auth.py", AUTH)
    w("backend/validators.py", VALIDATORS)
    w("backend/policies.py", POLICIES)
    w("backend/locks.py", LOCKS)
    w("backend/audit_svc.py", AUDIT)
    w("backend/dashboard_svc.py", DASHBOARD)
    w("backend/assets_svc.py", ASSETS)
    w("backend/screens_svc.py", SCREENS)
    w("backend/zones_svc.py", ZONES)
    w("backend/playlists_svc.py", PLAYLISTS)
    w("backend/windows_svc.py", WINDOWS)
    w("backend/publish_svc.py", PUBLISH)
    w("backend/panic_svc.py", PANIC)
    w("backend/overrides_svc.py", OVERRIDES)
    w("backend/evaluate_svc.py", EVALUATE)
    w("backend/history_svc.py", HISTORY)
    w("backend/layouts_svc.py", LAYOUTS)
    w("backend/stubs_svc.py", STUBS)
    w("backend/app.py", APP)

    for name, body in FIXTURES.items():
        w(f"fixtures/{name}", body)

    w("frontend/index.html", INDEX_HTML)
    w("frontend/css/app.css", APP_CSS)
    w("frontend/js/api.js", API_JS)
    w("frontend/js/app.js", APP_JS)
    for name, body in VIEWS.items():
        w(f"frontend/js/views/{name}", body)

    w("tests/test_smoke.py", TEST_SMOKE)
    w("tests/test_paths.py", TEST_PATHS)
    print("DONE root=", ROOT)


COUNT_LOC = '''
"""统计业务源码行数（不含 vendor / tests / Docker / README）。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {"node_modules", "__pycache__", ".pytest_cache", "tests", "scripts", ".git", "data"}
SKIP_NAMES = {"vue.global.prod.js", "README.md", "Dockerfile"}


def main() -> None:
    total = 0
    by: dict[str, int] = {}
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if set(p.relative_to(ROOT).parts) & SKIP_PARTS:
            continue
        if p.name in SKIP_NAMES or p.suffix == ".md" or p.name.startswith("_build"):
            continue
        if p.suffix in {".py", ".js", ".html", ".css"} or (p.suffix == ".json" and "fixtures" in p.parts):
            n = len(p.read_text(encoding="utf-8").splitlines())
            total += n
            by[p.suffix] = by.get(p.suffix, 0) + n
    print("业务 LOC 合计:", total)
    for k, v in sorted(by.items()):
        print(f"  {k}: {v}")
    print("达标:" if total >= 3000 else "未达标（须 >= 3000）", total >= 3000)


if __name__ == "__main__":
    main()
'''

MODELS = r'''
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
'''

DB = r'''
"""SQLite 初始化与种子。"""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

from models import DOMAIN, PRODUCT_NAME, SKELETON, SUB_DIRECTION, USERS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB_PATH = DATA / "app.db"
FIXTURES = ROOT / "fixtures"
FRONTEND = ROOT / "frontend"

PRODUCT_META = {
    "name": PRODUCT_NAME,
    "skeleton": SKELETON,
    "domain": DOMAIN,
    "sub": SUB_DIRECTION,
}


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS zones(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  zone_type TEXT NOT NULL,
  risk_level INTEGER NOT NULL DEFAULT 2,
  floor_label TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS screens(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  zone_id INTEGER NOT NULL REFERENCES zones(id),
  resolution TEXT NOT NULL,
  status TEXT NOT NULL,
  orientation TEXT NOT NULL DEFAULT 'landscape',
  note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS assets(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  kind TEXT NOT NULL,
  duration_sec INTEGER NOT NULL,
  resolution TEXT NOT NULL,
  status TEXT NOT NULL,
  owner TEXT NOT NULL,
  created_at REAL NOT NULL,
  checksum TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS layouts(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  slots_json TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS playlists(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  transition TEXT NOT NULL DEFAULT 'cut',
  loop_flag INTEGER NOT NULL DEFAULT 1,
  owner TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS playlist_items(
  id INTEGER PRIMARY KEY,
  playlist_id INTEGER NOT NULL REFERENCES playlists(id),
  asset_id INTEGER NOT NULL REFERENCES assets(id),
  seq INTEGER NOT NULL,
  dwell_sec INTEGER NOT NULL,
  UNIQUE(playlist_id, seq)
);
CREATE TABLE IF NOT EXISTS time_windows(
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  start_hm TEXT NOT NULL,
  end_hm TEXT NOT NULL,
  weekdays TEXT NOT NULL,
  status TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS publications(
  id INTEGER PRIMARY KEY,
  screen_id INTEGER NOT NULL REFERENCES screens(id),
  playlist_id INTEGER NOT NULL REFERENCES playlists(id),
  window_id INTEGER NOT NULL REFERENCES time_windows(id),
  layout_id INTEGER REFERENCES layouts(id),
  version INTEGER NOT NULL,
  summary TEXT NOT NULL,
  status TEXT NOT NULL,
  official INTEGER NOT NULL DEFAULT 1,
  published_at REAL,
  published_by TEXT,
  UNIQUE(screen_id, official)
);
CREATE TABLE IF NOT EXISTS publish_shadows(
  id INTEGER PRIMARY KEY,
  screen_id INTEGER NOT NULL REFERENCES screens(id),
  playlist_id INTEGER NOT NULL REFERENCES playlists(id),
  window_id INTEGER NOT NULL REFERENCES time_windows(id),
  layout_id INTEGER REFERENCES layouts(id),
  summary TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS panic_events(
  id INTEGER PRIMARY KEY,
  screen_id INTEGER NOT NULL REFERENCES screens(id),
  reason TEXT NOT NULL,
  official INTEGER NOT NULL DEFAULT 1,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS panic_shadows(
  id INTEGER PRIMARY KEY,
  screen_id INTEGER NOT NULL REFERENCES screens(id),
  reason TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS overrides(
  id INTEGER PRIMARY KEY,
  screen_id INTEGER NOT NULL REFERENCES screens(id),
  effect TEXT NOT NULL,
  playlist_id INTEGER REFERENCES playlists(id),
  asset_id INTEGER REFERENCES assets(id),
  note TEXT NOT NULL DEFAULT '',
  official INTEGER NOT NULL DEFAULT 1,
  active INTEGER NOT NULL DEFAULT 1,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS override_shadows(
  id INTEGER PRIMARY KEY,
  screen_id INTEGER NOT NULL REFERENCES screens(id),
  effect TEXT NOT NULL,
  playlist_id INTEGER REFERENCES playlists(id),
  asset_id INTEGER REFERENCES assets(id),
  note TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL,
  created_at REAL NOT NULL,
  created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS change_history(
  id INTEGER PRIMARY KEY,
  entity_kind TEXT NOT NULL,
  entity_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  detail TEXT NOT NULL,
  actor TEXT NOT NULL,
  created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS write_locks(
  id INTEGER PRIMARY KEY,
  lock_key TEXT UNIQUE NOT NULL,
  holder TEXT NOT NULL,
  expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_log(
  id INTEGER PRIMARY KEY,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at REAL NOT NULL
);
"""


def _load_json(name: str):
    path = FIXTURES / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _seed(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) c FROM zones").fetchone()["c"]:
        return
    now = time.time()
    for z in _load_json("zones.json"):
        conn.execute(
            "INSERT INTO zones(code,title,zone_type,risk_level,floor_label) VALUES(?,?,?,?,?)",
            (z["code"], z["title"], z["zone_type"], z["risk_level"], z.get("floor_label", "")),
        )
    zone_map = {r["code"]: r["id"] for r in conn.execute("SELECT id,code FROM zones")}
    for s in _load_json("screens.json"):
        conn.execute(
            "INSERT INTO screens(code,title,zone_id,resolution,status,orientation,note) VALUES(?,?,?,?,?,?,?)",
            (
                s["code"],
                s["title"],
                zone_map[s["zone_code"]],
                s["resolution"],
                s["status"],
                s.get("orientation", "landscape"),
                s.get("note", ""),
            ),
        )
    for a in _load_json("assets.json"):
        conn.execute(
            "INSERT INTO assets(code,title,kind,duration_sec,resolution,status,owner,created_at,checksum) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                a["code"],
                a["title"],
                a["kind"],
                a["duration_sec"],
                a["resolution"],
                a["status"],
                a["owner"],
                now - a.get("age_hours", 1) * 3600,
                a.get("checksum", ""),
            ),
        )
    for lay in _load_json("layouts.json"):
        conn.execute(
            "INSERT INTO layouts(code,title,slots_json,note) VALUES(?,?,?,?)",
            (lay["code"], lay["title"], json.dumps(lay["slots"], ensure_ascii=False), lay.get("note", "")),
        )
    for p in _load_json("playlists.json"):
        conn.execute(
            "INSERT INTO playlists(code,title,status,transition,loop_flag,owner,created_at) VALUES(?,?,?,?,?,?,?)",
            (
                p["code"],
                p["title"],
                p["status"],
                p.get("transition", "cut"),
                1 if p.get("loop", True) else 0,
                p["owner"],
                now,
            ),
        )
    pl_map = {r["code"]: r["id"] for r in conn.execute("SELECT id,code FROM playlists")}
    asset_map = {r["code"]: r["id"] for r in conn.execute("SELECT id,code FROM assets")}
    for item in _load_json("playlist_items.json"):
        conn.execute(
            "INSERT INTO playlist_items(playlist_id,asset_id,seq,dwell_sec) VALUES(?,?,?,?)",
            (pl_map[item["playlist_code"]], asset_map[item["asset_code"]], item["seq"], item["dwell_sec"]),
        )
    for wrow in _load_json("time_windows.json"):
        conn.execute(
            "INSERT INTO time_windows(code,title,start_hm,end_hm,weekdays,status,note) VALUES(?,?,?,?,?,?,?)",
            (
                wrow["code"],
                wrow["title"],
                wrow["start_hm"],
                wrow["end_hm"],
                wrow["weekdays"],
                wrow["status"],
                wrow.get("note", ""),
            ),
        )
    screen_map = {r["code"]: r["id"] for r in conn.execute("SELECT id,code FROM screens")}
    window_map = {r["code"]: r["id"] for r in conn.execute("SELECT id,code FROM time_windows")}
    layout_map = {r["code"]: r["id"] for r in conn.execute("SELECT id,code FROM layouts")}
    for pub in _load_json("publications.json"):
        conn.execute(
            "INSERT INTO publications(screen_id,playlist_id,window_id,layout_id,version,summary,status,official,published_at,published_by) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (
                screen_map[pub["screen_code"]],
                pl_map[pub["playlist_code"]],
                window_map[pub["window_code"]],
                layout_map.get(pub.get("layout_code")) if pub.get("layout_code") else None,
                pub.get("version", 1),
                pub["summary"],
                pub["status"],
                1,
                now,
                pub.get("published_by", "admin"),
            ),
        )
    for h in _load_json("change_history.json"):
        conn.execute(
            "INSERT INTO change_history(entity_kind,entity_id,action,detail,actor,created_at) VALUES(?,?,?,?,?,?)",
            (h["entity_kind"], h["entity_id"], h["action"], h["detail"], h["actor"], now - h.get("age_hours", 1) * 3600),
        )
    conn.commit()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        _seed(conn)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows) -> list[dict]:
    return [dict(r) for r in rows]
'''

# Continue in part 2 - the file is getting large. I'll split into multiple write calls in the script by importing from part files, OR continue appending more string constants in the same file.

# Actually the Write tool might have limits. Let me split into _build_signboard_part2.py for services and frontend.
print("part1 constants defined in builder - continuing via part files")
