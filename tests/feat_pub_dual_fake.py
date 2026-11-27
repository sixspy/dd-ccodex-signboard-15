# -*- coding: utf-8 -*-
"""signboard-15 红测乙：求值服务不得把同屏双正式版本都当成生效（假绿）。

事故态：无锁双写后同屏出现两行 official=1 的正式发布，在线求值在两个版本间
跳动，屏幕却显示一切正常（假绿灯）。

钉死口径：
- 同屏正式发布唯一是求值可信的前置；出现双正式必须显式报冲突（500/409 级错误，
  响应 detail 含“正式发布不唯一”），严禁静默 fetchone 挑一行继续返回 source=publication。
- 正式唯一时求值仍返回真实生效版本，业务不回退。
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(ROOT / "backend"))

from db import init_db  # noqa: E402
from app import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db(tmp_path, monkeypatch):
    db = tmp_path / "app.db"
    monkeypatch.setattr("db.DB_PATH", db)
    monkeypatch.setattr("db.DATA", tmp_path)
    if db.exists():
        db.unlink()
    init_db()
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _login(client, username="admin", password="admin123"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _side_refs(client, headers):
    screens = client.get("/api/screens", headers=headers).json()["items"]
    side = next(s for s in screens if s["code"] == "scr_lobby_side")
    playlists = client.get("/api/playlists", headers=headers).json()["items"]
    pl_a = next(p for p in playlists if p["code"] == "pl_lift_loop")
    pl_b = next(p for p in playlists if p["code"] == "pl_lobby_day")
    windows = client.get("/api/windows", headers=headers).json()["items"]
    win = next(w for w in windows if w["code"] == "win_workday")
    return side, pl_a, pl_b, win


def _inject_dual_official(db_path, side, pl_a, pl_b, win):
    """复刻无锁事故：同屏两行正式发布并存（版本跳动现场）。"""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys=ON")
        # 临时撤掉唯一约束，制造事故现场（现场库正是无锁双写留下的账）
        conn.execute("PRAGMA ignore_check_constraints=ON")
        conn.executescript(
            """
            CREATE TABLE publications_dual AS SELECT * FROM publications WHERE 0;
            INSERT INTO publications_dual SELECT * FROM publications;
            DROP TABLE publications;
            CREATE TABLE publications(
              id INTEGER PRIMARY KEY,
              screen_id INTEGER NOT NULL,
              playlist_id INTEGER NOT NULL,
              window_id INTEGER NOT NULL,
              layout_id INTEGER,
              version INTEGER NOT NULL,
              summary TEXT NOT NULL,
              status TEXT NOT NULL,
              official INTEGER NOT NULL DEFAULT 1,
              published_at REAL,
              published_by TEXT
            );
            INSERT INTO publications SELECT * FROM publications_dual;
            DROP TABLE publications_dual;
            """
        )
        import time

        for version, pl, summary in (
            (5, pl_a, "事故双正式版本五"),
            (6, pl_b, "事故双正式版本六"),
        ):
            conn.execute(
                """
                INSERT INTO publications(screen_id,playlist_id,window_id,layout_id,version,
                  summary,status,official,published_at,published_by)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    side["id"], pl["id"], win["id"], None, version, summary,
                    "published", 1, time.time(), "writer",
                ),
            )
        conn.commit()
        n = conn.execute(
            "SELECT COUNT(*) FROM publications WHERE screen_id=? AND official=1",
            (side["id"],),
        ).fetchone()[0]
        assert n == 2
    finally:
        conn.close()


def test_evaluate_rejects_dual_official_instead_of_fake_green(client, tmp_path):
    h = _login(client)
    side, pl_a, pl_b, win = _side_refs(client, h)
    db_path = next(Path(tmp_path).glob("app.db"))
    _inject_dual_official(db_path, side, pl_a, pl_b, win)

    ev = client.post(
        "/api/evaluate/screen",
        headers=h,
        json={"screen_id": side["id"], "now_hm": "10:00", "weekday": "1"},
    )
    # 假绿红灯：双正式并存时禁止返回 200 的 source=publication
    assert ev.status_code in (409, 500), ev.text
    assert "正式发布不唯一" in ev.json()["detail"]
    assert ev.json().get("source") != "publication"


def test_evaluate_still_works_when_official_unique(client):
    """账实唯一时求值照常返回生效版本，防止修事故修挂正常链路。"""
    h = _login(client, "writer", "writer123")
    side, pl_a, _pl_b, win = _side_refs(client, h)
    r = client.post(
        "/api/publish/official",
        headers=h,
        json={
            "screen_id": side["id"],
            "playlist_id": pl_a["id"],
            "window_id": win["id"],
            "summary": "唯一正式发布",
        },
    )
    assert r.status_code == 200, r.text
    version = r.json()["version"]
    ev = client.post(
        "/api/evaluate/screen",
        headers=h,
        json={"screen_id": side["id"], "now_hm": "10:00", "weekday": "1"},
    )
    assert ev.status_code == 200, ev.text
    body = ev.json()
    assert body["source"] == "publication"
    assert body["version"] == version


def test_dual_official_versions_must_not_both_evaluate(client, tmp_path):
    """连续求值不得在双版本间跳动：每次都必须是同一个冲突错误。"""
    h = _login(client)
    side, pl_a, pl_b, win = _side_refs(client, h)
    db_path = next(Path(tmp_path).glob("app.db"))
    _inject_dual_official(db_path, side, pl_a, pl_b, win)

    codes, details = set(), set()
    for _ in range(5):
        ev = client.post(
            "/api/evaluate/screen",
            headers=h,
            json={"screen_id": side["id"], "now_hm": "10:00", "weekday": "1"},
        )
        codes.add(ev.status_code)
        details.add(ev.json()["detail"])
    assert codes <= {409, 500}
    assert len(details) == 1, f"错误口径须稳定，实际：{details}"
