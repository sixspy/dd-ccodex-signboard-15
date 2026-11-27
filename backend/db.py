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
