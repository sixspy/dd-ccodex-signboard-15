"""主链路冒烟。"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 使用临时库
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(ROOT / "backend"))

from db import DB_PATH, DATA, init_db  # noqa: E402
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
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["domain"] == "应用开发"
    assert body["screens"] >= 1


def test_dashboard_and_seed(client):
    h = _login(client)
    d = client.get("/api/dashboard", headers=h).json()
    assert d["ready_assets"] >= 1
    assert d["official_publications"] >= 1
    assets = client.get("/api/assets", headers=h).json()["items"]
    assert any(a["code"] == "img_welcome" for a in assets)


def test_publish_official_and_evaluate(client):
    h = _login(client, "writer", "writer123")
    # 使用已有可播清单与时段，换到侧屏
    screens = client.get("/api/screens", headers=h).json()["items"]
    side = next(s for s in screens if s["code"] == "scr_lobby_side")
    playlists = client.get("/api/playlists", headers=h).json()["items"]
    pl = next(p for p in playlists if p["code"] == "pl_lift_loop")
    windows = client.get("/api/windows", headers=h).json()["items"]
    win = next(w for w in windows if w["code"] == "win_workday")
    r = client.post(
        "/api/publish/official",
        headers=h,
        json={
            "screen_id": side["id"],
            "playlist_id": pl["id"],
            "window_id": win["id"],
            "summary": "侧屏正式发布",
        },
    )
    assert r.status_code == 200, r.text
    ev = client.post(
        "/api/evaluate/screen",
        headers=h,
        json={"screen_id": side["id"], "now_hm": "10:00", "weekday": "1"},
    )
    assert ev.status_code == 200
    assert ev.json()["source"] == "publication"


def test_shadow_promote_path(client):
    h = _login(client)
    screens = client.get("/api/screens", headers=h).json()["items"]
    target = next(s for s in screens if s["code"] == "scr_corr_c2")
    # 先上线
    client.patch(f"/api/screens/{target['id']}", headers=h, json={"status": "online"})
    playlists = client.get("/api/playlists", headers=h).json()["items"]
    pl = next(p for p in playlists if p["code"] == "pl_lobby_day")
    windows = client.get("/api/windows", headers=h).json()["items"]
    win = next(w for w in windows if w["code"] == "win_evening")
    sh = client.post(
        "/api/publish/shadow",
        headers=h,
        json={
            "screen_id": target["id"],
            "playlist_id": pl["id"],
            "window_id": win["id"],
            "summary": "走廊影子草案",
        },
    )
    assert sh.status_code == 200, sh.text
    sid = sh.json()["id"]
    pr = client.post(f"/api/publish/shadow/{sid}/promote", headers=h, json={})
    assert pr.status_code == 200, pr.text


def test_stubs_501(client):
    h = _login(client)
    r = client.post("/api/stubs/remote_push", headers=h, json={"screen_id": 1})
    assert r.status_code == 501
