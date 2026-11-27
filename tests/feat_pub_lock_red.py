# -*- coding: utf-8 -*-
"""signboard-15 红测甲：同屏第二笔正式发布必须整笔拒写并记争用。

口径（甲路径，锁死不得与乙路径混用）：
- 同屏正式发布互斥：同屏同时只允许一笔正式发布成功，败方整笔拒写（HTTP 409）。
- 败方正式区零增：publications 同屏 official=1 恒为一行，版本不回退不并立。
- 败方只留争用痕：audit_log 落 publish.contention，change_history 留 contention 痕，
  不得借影子草案/角标闪烁交差（publish_shadows 零增）。
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(ROOT / "backend"))

from db import init_db  # noqa: E402
from app import app  # noqa: E402
from feat_pub_race import _LockReadInterleaver  # noqa: E402


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


def _login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _side_screen_refs(client, headers):
    screens = client.get("/api/screens", headers=headers).json()["items"]
    side = next(s for s in screens if s["code"] == "scr_lobby_side")
    playlists = client.get("/api/playlists", headers=headers).json()["items"]
    pl = next(p for p in playlists if p["code"] == "pl_lift_loop")
    windows = client.get("/api/windows", headers=headers).json()["items"]
    win = next(w for w in windows if w["code"] == "win_workday")
    return side, pl, win


def _payload(side, pl, win, summary):
    return {
        "screen_id": side["id"],
        "playlist_id": pl["id"],
        "window_id": win["id"],
        "summary": summary,
    }


def _official_count(db, screen_id):
    import sqlite3

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        n = conn.execute(
            "SELECT COUNT(*) c FROM publications WHERE screen_id=? AND official=1",
            (screen_id,),
        ).fetchone()[0]
        versions = [
            r[0]
            for r in conn.execute(
                "SELECT version FROM publications WHERE screen_id=? AND official=1 ORDER BY version",
                (screen_id,),
            ).fetchall()
        ]
        shadow_n = conn.execute(
            "SELECT COUNT(*) c FROM publish_shadows WHERE screen_id=?",
            (screen_id,),
        ).fetchone()[0]
        actions = [
            r[0]
            for r in conn.execute(
                "SELECT action FROM change_history WHERE entity_kind='publish_contention'"
            ).fetchall()
        ]
        audit_actions = [
            r[0] for r in conn.execute("SELECT action FROM audit_log").fetchall()
        ]
    finally:
        conn.close()
    return n, versions, shadow_n, actions, audit_actions


def test_concurrent_second_official_rejected_and_traced(client, tmp_path):
    """同屏双会话同时正式上屏：仅一成，败方整笔 409 且只留争用痕。"""
    h_admin = _login(client, "admin", "admin123")
    h_writer = _login(client, "writer", "writer123")
    side, pl, win = _side_screen_refs(client, h_admin)
    body_a = _payload(side, pl, win, "双发甲笔正式")
    body_b = _payload(side, pl, win, "双发乙笔正式")

    outcomes: list[dict] = []
    errors: list[BaseException] = []
    interleaver = _LockReadInterleaver()
    interleaver.install()

    def call(headers, body):
        try:
            r = client.post("/api/publish/official", headers=headers, json=body)
            outcomes.append({"status": r.status_code, "body": r.json() if r.content else {}})
        except BaseException as exc:  # noqa: BLE001 测试须暴露线程内异常
            errors.append(exc)

    try:
        t1 = threading.Thread(target=call, args=(h_admin, body_a))
        t2 = threading.Thread(target=call, args=(h_writer, body_b))
        t1.start()
        t2.start()
        interleaver.release_gate()
        t1.join(15)
        t2.join(15)
    finally:
        interleaver.restore()

    assert not errors, f"并发请求线程异常：{errors!r}"
    assert len(outcomes) == 2, "两路正式发布均须返回，不得挂死"
    statuses = sorted(o["status"] for o in outcomes)
    # 甲路径闸口：一成一拒，禁止双 200 并存
    assert statuses == [200, 409], f"同屏双发必须互斥，实际：{statuses}"
    loser = next(o for o in outcomes if o["status"] == 409)
    assert "争用" in str(loser["body"].get("detail", "")), loser["body"]

    db = next(Path(tmp_path).glob("app.db"))
    n, versions, shadow_n, hist_actions, audit_actions = _official_count(db, side["id"])
    # 正式区零增：同屏仅一行正式发布
    assert n == 1, f"同屏正式发布必须唯一，实际 {n} 行并存"
    assert len(versions) == 1
    # 败方不得借乙路径落影子草案
    assert shadow_n == 0, "甲路径败方不得产生影子草案"
    # 败方只留争用痕
    assert "contention" in " ".join(audit_actions), f"审计缺争用痕：{audit_actions}"
    assert any("contention" in a for a in hist_actions), f"历史缺争用痕：{hist_actions}"


def test_same_holder_second_claim_is_still_rejected(client, tmp_path):
    """同账号两笔同屏正式发布也互斥：持有者名字相同不等于同一笔事务。"""
    h = _login(client, "writer", "writer123")
    side, pl, win = _side_screen_refs(client, h)

    import locks

    # 同屏已有一笔同账号在途事务持锁，第二笔不得重入夺权
    locks.acquire(f"publish:{side['id']}", "writer")
    try:
        r = client.post(
            "/api/publish/official", headers=h, json=_payload(side, pl, win, "同持锁第二笔")
        )
        assert r.status_code == 409, r.text
    finally:
        locks.release(f"publish:{side['id']}", "writer")

    db = next(Path(tmp_path).glob("app.db"))
    n, _versions, shadow_n, _hist, _audit = _official_count(db, side["id"])
    assert n == 0, "被拒的第二笔不得写入正式区"
    assert shadow_n == 0, "被拒的第二笔不得落影子草案"


def test_loser_leaves_no_official_and_no_shadow(client, tmp_path):
    """争用败方：正式零增、影子零增，只留痕。"""
    h_admin = _login(client, "admin", "admin123")
    h_writer = _login(client, "writer", "writer123")
    side, pl, win = _side_screen_refs(client, h_admin)

    import locks

    # 模拟同屏另一会话已持锁在途
    locks.acquire(f"publish:{side['id']}", "admin")
    try:
        r = client.post(
            "/api/publish/official",
            headers=h_writer,
            json=_payload(side, pl, win, "败方候选正式"),
        )
        assert r.status_code == 409, r.text
    finally:
        locks.release(f"publish:{side['id']}", "admin")

    db = next(Path(tmp_path).glob("app.db"))
    n, _versions, shadow_n, _hist, audit_actions = _official_count(db, side["id"])
    assert n == 0, "大堂侧屏本无正式发布，败方不得让正式区出现任何行"
    assert shadow_n == 0, "败方不得落影子发布草案"
    assert "publish.contention" in audit_actions
