# -*- coding: utf-8 -*-
"""signboard-15 红测争用：两路抢「同屏正式发布互斥」，无锁双成即事故。

本文件只锁并发位，不并入甲乙正确性口径：
- 两个写会话同屏同时正式上屏，无锁时双 200 双成 → 红；
- 命令行对打 race_screen_pub_lock 必须可执行且能据互斥口径判定；
- 发布互斥与正式唯一须同事务联查跨表账实（publications / write_locks /
  audit_log / change_history / publish_shadows）。
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("PYTHONPATH", str(ROOT / "backend"))

import locks as locks_mod  # noqa: E402
from db import init_db  # noqa: E402
from app import app  # noqa: E402

CLI = ROOT / "scripts" / "race_screen_pub_lock.py"


class _LockReadInterleaver:
    """在锁服务访问 write_locks 的首条语句处制造确定性双路交会。

    旧实现 SELECT 先行、新实现 INSERT 先行，故不挑语句类型；用开始闸门+到齐
    事件替代 Barrier，避免线程池里一路先到先超时把屏障打烂。
    """

    def __init__(self, parties: int = 2, hold_sec: float = 1.0):
        self.parties = parties
        self.hold_sec = hold_sec
        self.start = threading.Event()
        self.arrivals = 0
        self.all_arrived = threading.Event()
        self._counter_lock = threading.Lock()
        self._orig_connect = None

    def install(self) -> None:
        outer = self
        orig_connect = locks_mod.connect

        class _InterceptConn:
            def __init__(self, inner=None):
                self._inner = inner if inner is not None else orig_connect()

            def __getattr__(self, name):
                return getattr(self._inner, name)

            def __enter__(self):
                self._inner.__enter__()
                return self

            def __exit__(self, exc_type, exc, tb):
                return self._inner.__exit__(exc_type, exc, tb)

            def execute(self, sql, params=()):
                if isinstance(sql, str) and "write_locks" in sql:
                    outer.start.wait(timeout=5)
                    with outer._counter_lock:
                        outer.arrivals += 1
                        if outer.arrivals >= outer.parties:
                            outer.all_arrived.set()
                    # 两路到齐后再各自执行，同键写保留由数据库原子裁决
                    outer.all_arrived.wait(timeout=5)
                    time.sleep(outer.hold_sec)
                return self._inner.execute(sql, params)

        def _patched():
            return _InterceptConn(orig_connect())

        self._orig_connect = orig_connect
        locks_mod.connect = _patched

    def release_gate(self) -> None:
        self.start.set()

    def restore(self) -> None:
        locks_mod.connect = self._orig_connect


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


def _side_payload(client, headers):
    screens = client.get("/api/screens", headers=headers).json()["items"]
    side = next(s for s in screens if s["code"] == "scr_lobby_side")
    playlists = client.get("/api/playlists", headers=headers).json()["items"]
    pl = next(p for p in playlists if p["code"] == "pl_lift_loop")
    windows = client.get("/api/windows", headers=headers).json()["items"]
    win = next(w for w in windows if w["code"] == "win_workday")
    return side, {
        "screen_id": side["id"],
        "playlist_id": pl["id"],
        "window_id": win["id"],
        "summary": "争用红测双发",
    }


def test_two_sessions_race_only_one_wins(client):
    """无锁双成事故位：同屏并发正式发布必须恰好一成（确定性交错，不靠 timing）。"""
    h_a = _login(client, "admin", "admin123")
    h_b = _login(client, "writer", "writer123")
    side, payload = _side_payload(client, h_a)
    interleaver = _LockReadInterleaver()
    interleaver.install()
    outcomes: list[int] = []
    errors: list[BaseException] = []

    def strike(headers):
        try:
            outcomes.append(
                client.post("/api/publish/official", headers=headers, json=payload).status_code
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    try:
        t1 = threading.Thread(target=strike, args=(h_a,))
        t2 = threading.Thread(target=strike, args=(h_b,))
        t1.start()
        t2.start()
        interleaver.release_gate()
        t1.join(15)
        t2.join(15)
    finally:
        interleaver.restore()

    assert not errors, f"并发请求线程异常：{errors!r}"
    assert sorted(outcomes) == [200, 409], f"双成/异常即事故：{outcomes}"


def test_same_account_race_is_also_mutually_exclusive(client, tmp_path):
    """同账号双会话同屏抢锁也禁止双成（持锁名相同不是重入理由）。"""
    h1 = _login(client, "writer", "writer123")
    h2 = _login(client, "writer", "writer123")
    side, payload = _side_payload(client, h1)
    interleaver = _LockReadInterleaver()
    interleaver.install()
    outcomes: list[int] = []
    errors: list[BaseException] = []

    def strike(headers):
        try:
            outcomes.append(
                client.post("/api/publish/official", headers=headers, json=payload).status_code
            )
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    try:
        t1 = threading.Thread(target=strike, args=(h1,))
        t2 = threading.Thread(target=strike, args=(h2,))
        t1.start()
        t2.start()
        interleaver.release_gate()
        t1.join(15)
        t2.join(15)
    finally:
        interleaver.restore()

    assert not errors, f"并发请求线程异常：{errors!r}"
    assert sorted(outcomes) == [200, 409], f"同账号双会话仍须互斥：{outcomes}"
    db = next(Path(tmp_path).glob("app.db"))
    conn = sqlite3.connect(db)
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM publications WHERE screen_id=? AND official=1",
            (side["id"],),
        ).fetchone()[0]
    finally:
        conn.close()
    assert n == 1


def test_cross_table_ledger_in_one_transaction(client, tmp_path):
    """同事务联查跨表账实：正式唯一、败方痕在、影子零增、锁无残留。"""
    h_a = _login(client, "admin", "admin123")
    h_b = _login(client, "writer", "writer123")
    side, payload = _side_payload(client, h_a)

    import locks

    # 在途锁：败方这一笔
    locks.acquire(f"publish:{side['id']}", "admin")
    try:
        r = client.post("/api/publish/official", headers=h_b, json=payload)
        assert r.status_code == 409
    finally:
        locks.release(f"publish:{side['id']}", "admin")

    # 胜方这一笔随后成功
    r2 = client.post("/api/publish/official", headers=h_a, json=payload)
    assert r2.status_code == 200, r2.text

    db = next(Path(tmp_path).glob("app.db"))
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        pubs = conn.execute(
            "SELECT id, version FROM publications WHERE screen_id=? AND official=1",
            (side["id"],),
        ).fetchall()
        stale = conn.execute(
            "SELECT COUNT(*) c FROM write_locks WHERE lock_key=?",
            (f"publish:{side['id']}",),
        ).fetchone()["c"]
        contention_audit = conn.execute(
            "SELECT COUNT(*) c FROM audit_log WHERE action='publish.contention'"
        ).fetchone()["c"]
        contention_hist = conn.execute(
            "SELECT COUNT(*) c FROM change_history "
            "WHERE action='publish.contention' AND entity_kind='publish_contention'"
        ).fetchone()["c"]
        shadows = conn.execute(
            "SELECT COUNT(*) c FROM publish_shadows WHERE screen_id=?",
            (side["id"],),
        ).fetchone()["c"]
    finally:
        conn.close()

    assert len(pubs) == 1, f"正式唯一账实不符：{pubs}"
    assert stale == 0, "锁残留，事务未收口"
    assert contention_audit >= 1, "审计服务缺争用痕"
    assert contention_hist >= 1, "历史服务缺争用痕"
    assert shadows == 0, "败方不得落影子发布草案"


def test_race_cli_command_runs_and_guards(tmp_path):
    """对打命令行 race_screen_pub_lock 可执行，红态须以非零退出码报事故。"""
    assert CLI.exists(), "对打命令行脚本必须随案交付"
    db_file = tmp_path / "cli_race.db"
    proc = subprocess.run(
        [sys.executable, str(CLI), "--db", str(db_file), "--rounds", "2"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = proc.stdout + proc.stderr
    assert "race_screen_pub_lock" in out or "对打" in out
    assert "RESULT" in out
    # 闸口封死前（无可靠互斥）对打必须报 FAIL；修复后须为 PASS。
    # 红阶段断言非零，绿阶段本测试随实现转绿（退出码 0）。
    assert proc.returncode in (0, 1)
    if proc.returncode == 1:
        assert "FAIL" in out
    else:
        assert "PASS" in out
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM publications WHERE official=1 "
                "AND screen_id=(SELECT id FROM screens WHERE code='scr_lobby_side')"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n == 1
