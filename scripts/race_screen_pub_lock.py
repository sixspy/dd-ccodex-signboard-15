# -*- coding: utf-8 -*-
"""对打命令行：race_screen_pub_lock。

现场复现「同屏双会话同时正式上屏」：两个写账号在同一进程内用线程屏障对齐，
同时对大堂侧屏（scr_lobby_side）发起正式发布，核验 signboard-15 互斥口径：

  1. 恰好一笔 200 成功、一笔 409 争用拒写（禁止双成、禁止 500 裸库错）；
  2. publications 同屏 official=1 恒为一行（正式唯一，账实相符）；
  3. 败方零正式增、零影子草案，只留 audit_log/change_history 争用痕；
  4. 事务收口后 write_locks 无残留锁。

用法：
  python scripts/race_screen_pub_lock.py [--db /tmp/race.db] [--rounds 3]

退出码：0=互斥口径成立；1=现场复现事故（双成/假绿/账实不符）。
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def _bootstrap(db_path: Path):
    os.environ["SB_RACE_DB"] = str(db_path)
    import db as db_mod

    db_mod.DB_PATH = db_path
    db_mod.DATA = db_path.parent
    if db_path.exists():
        db_path.unlink()
    db_mod.init_db()

    from app import app  # noqa: F401
    from fastapi.testclient import TestClient

    return TestClient(app)


def _login(client, username: str, password: str) -> dict:
    r = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _refs(client, headers):
    screens = client.get("/api/screens", headers=headers).json()["items"]
    side = next(s for s in screens if s["code"] == "scr_lobby_side")
    playlists = client.get("/api/playlists", headers=headers).json()["items"]
    pl = next(p for p in playlists if p["code"] == "pl_lift_loop")
    windows = client.get("/api/windows", headers=headers).json()["items"]
    win = next(w for w in windows if w["code"] == "win_workday")
    return side, pl, win


def _ledger(db_path: Path, screen_id: int) -> dict:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, version FROM publications WHERE screen_id=? AND official=1 ORDER BY id",
            (screen_id,),
        ).fetchall()
        locks = conn.execute(
            "SELECT lock_key, holder FROM write_locks WHERE lock_key=?",
            (f"publish:{screen_id}",),
        ).fetchall()
        contentions = conn.execute(
            "SELECT COUNT(*) c FROM audit_log WHERE action='publish.contention'"
        ).fetchone()[0]
        history_marks = conn.execute(
            "SELECT COUNT(*) c FROM change_history "
            "WHERE action='publish.contention' AND entity_kind='publish_contention'"
        ).fetchone()[0]
        shadows = conn.execute(
            "SELECT COUNT(*) c FROM publish_shadows WHERE screen_id=?",
            (screen_id,),
        ).fetchone()[0]
    finally:
        conn.close()
    return {
        "official_rows": rows,
        "stale_locks": locks,
        "contention_audit": contentions,
        "contention_history": history_marks,
        "shadows": shadows,
    }


def _install_gate(parties: int = 2, hold_sec: float = 1.0):
    """在锁服务访问 write_locks 的首条语句处制造确定性双路交会。"""
    import threading
    import time as _time

    import locks as locks_mod

    start = threading.Event()
    all_arrived = threading.Event()
    counter = {"n": 0}
    counter_lock = threading.Lock()
    orig_connect = locks_mod.connect

    class _GateConn:
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
                start.wait(timeout=5)
                with counter_lock:
                    counter["n"] += 1
                    if counter["n"] >= parties:
                        all_arrived.set()
                all_arrived.wait(timeout=5)
                _time.sleep(hold_sec)
            return self._inner.execute(sql, params)

    locks_mod.connect = _GateConn
    return start, lambda: setattr(locks_mod, "connect", orig_connect)


def run_round(db_path: Path) -> tuple[bool, list[str]]:
    client = _bootstrap(db_path)
    notes: list[str] = []
    ok = True
    with client:
        h_a = _login(client, "admin", "admin123")
        h_b = _login(client, "writer", "writer123")
        side, pl, win = _refs(client, h_a)
        payload = {
            "screen_id": side["id"],
            "playlist_id": pl["id"],
            "window_id": win["id"],
            "summary": "race_screen_pub_lock 对打",
        }
        gate, restore = _install_gate()
        outcomes: list[dict] = []

        def strike(headers):
            r = client.post("/api/publish/official", headers=headers, json=payload)
            outcomes.append({"status": r.status_code, "detail": r.text[:200]})

        t1 = threading.Thread(target=strike, args=(h_a,))
        t2 = threading.Thread(target=strike, args=(h_b,))
        try:
            t1.start()
            t2.start()
            gate.set()
            t1.join(20)
            t2.join(20)
        finally:
            restore()

    statuses = sorted(o["status"] for o in outcomes)
    notes.append(f"双发状态码：{statuses}（原始 {[o['status'] for o in outcomes]}）")
    if statuses != [200, 409]:
        ok = False
        notes.append("✗ 闸口失效：互斥要求一成(200)一拒(409)")

    ledger = _ledger(db_path, side["id"])
    notes.append(f"跨表账实：{ledger}")
    if len(ledger["official_rows"]) != 1:
        ok = False
        notes.append("✗ 正式区不唯一：同屏出现多行/零行正式发布")
    if ledger["shadows"] != 0:
        ok = False
        notes.append("✗ 败方落了影子草案，违反甲路径零影子")
    if ledger["contention_audit"] < 1 or ledger["contention_history"] < 1:
        ok = False
        notes.append("✗ 败方未留争用痕（audit_log/change_history）")
    if ledger["stale_locks"]:
        ok = False
        notes.append("✗ 事务收口后锁未释放")
    if ok:
        notes.append("✓ 同屏正式发布互斥成立，败方零正式只留痕")
    return ok, notes


def main() -> int:
    parser = argparse.ArgumentParser(description="同屏双发互斥对打 race_screen_pub_lock")
    parser.add_argument("--db", default="/tmp/race_screen_pub_lock.db")
    parser.add_argument("--rounds", type=int, default=3)
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    all_ok = True
    for i in range(1, args.rounds + 1):
        print(f"── 对打第 {i}/{args.rounds} 轮 ──")
        ok, notes = run_round(db_path)
        for n in notes:
            print(n)
        all_ok = all_ok and ok
    print("RESULT:", "PASS 互斥成立" if all_ok else "FAIL 事故复现，闸口未封死")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
