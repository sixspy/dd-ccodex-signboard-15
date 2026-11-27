"""写入短锁，防并发双写。

signboard-15：同屏正式发布互斥必须由数据库原子性兜底，禁止“先 SELECT 再
INSERT”的读改写——两路并发会同时读到空锁随后双写。这里改为 INSERT 先行：
- BEGIN IMMEDIATE 立即取得 SQLite 写保留，同键插入被 UNIQUE 约束串行裁决；
- 锁不可重入：同持有者的第二笔事务同样 409，禁止借同名夺权；
- 过期锁可被接管，TTL 内的活锁一律拒写并由调用方记争用痕。
"""
from __future__ import annotations

import sqlite3
import time
from fastapi import APIRouter, Header, HTTPException

from auth import current_user, require_writer
from db import connect

router = APIRouter(prefix="/api/locks", tags=["locks"])


class LockBusy(HTTPException):
    """争用拒写：锁仍被其他在途事务持有。"""

    def __init__(self, lock_key: str, holder: str):
        super().__init__(409, f"资源争用：{lock_key} 正被 {holder} 持锁在途，本笔整笔拒写")
        self.lock_key = lock_key
        self.holder = holder


def acquire(lock_key: str, holder: str, ttl_sec: int = 20) -> None:
    """抢占式加锁。成功返回；活锁冲突抛 409（含“争用”字样）。"""
    now = time.time()
    conn = connect()
    try:
        # 插入先行：写保留在语句执行瞬间裁决，杜绝读后写窗口
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower():
                raise LockBusy(lock_key, "其他在途写事务") from exc
            raise
        try:
            conn.execute(
                "INSERT INTO write_locks(lock_key,holder,expires_at) VALUES(?,?,?)",
                (lock_key, holder, now + ttl_sec),
            )
        except sqlite3.IntegrityError:
            row = conn.execute(
                "SELECT holder, expires_at FROM write_locks WHERE lock_key=?",
                (lock_key,),
            ).fetchone()
            if row is None:
                # 极端情况下行已被并发清掉，整笔重试由上层 409 保守拒写
                conn.rollback()
                raise HTTPException(409, f"资源争用：{lock_key} 锁状态翻转，本笔整笔拒写")
            if row["expires_at"] <= now:
                # 死锁/崩殂遗留：过期接管，仍在同一写事务内原子完成
                conn.execute(
                    "UPDATE write_locks SET holder=?, expires_at=? WHERE lock_key=?",
                    (holder, now + ttl_sec, lock_key),
                )
                conn.commit()
                return
            conn.rollback()
            raise LockBusy(lock_key, row["holder"])
        conn.commit()
    finally:
        conn.close()


def release(lock_key: str, holder: str) -> None:
    with connect() as conn:
        conn.execute(
            "DELETE FROM write_locks WHERE lock_key=? AND holder=?",
            (lock_key, holder),
        )
        conn.commit()


@router.post("/acquire")
def api_acquire(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    key = (body.get("lock_key") or "").strip()
    if not key:
        raise HTTPException(400, "缺少 lock_key")
    acquire(key, user["username"], int(body.get("ttl_sec") or 20))
    return {"ok": True, "lock_key": key, "holder": user["username"]}


@router.post("/release")
def api_release(body: dict, authorization: str | None = Header(default=None)):
    user = current_user(authorization)
    require_writer(user)
    key = (body.get("lock_key") or "").strip()
    release(key, user["username"])
    return {"ok": True}
