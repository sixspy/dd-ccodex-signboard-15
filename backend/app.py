"""楼宇数字标牌编排 — FastAPI 入口。"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from assets_svc import router as assets_router
from audit_svc import router as audit_router
from auth import router as auth_router
from dashboard_svc import router as dashboard_router
from db import FRONTEND, PRODUCT_META, init_db
from evaluate_svc import router as evaluate_router
from history_svc import router as history_router
from layouts_svc import router as layouts_router
from locks import router as locks_router
from overrides_svc import router as overrides_router
from panic_svc import router as panic_router
from playlists_svc import router as playlists_router
from publish_svc import router as publish_router
from screens_svc import router as screens_router
from stubs_svc import router as stubs_router
from windows_svc import router as windows_router
from zones_svc import router as zones_router

PRODUCT = PRODUCT_META["name"]
SKELETON = PRODUCT_META["skeleton"]

app = FastAPI(title=PRODUCT, description=SKELETON)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    auth_router,
    dashboard_router,
    zones_router,
    screens_router,
    assets_router,
    layouts_router,
    playlists_router,
    windows_router,
    publish_router,
    panic_router,
    overrides_router,
    evaluate_router,
    history_router,
    locks_router,
    audit_router,
    stubs_router,
):
    app.include_router(r)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    from db import DB_PATH, connect

    with connect() as conn:
        screens = conn.execute("SELECT COUNT(*) c FROM screens").fetchone()["c"]
        pubs = conn.execute(
            "SELECT COUNT(*) c FROM publications WHERE official=1 AND status='published'"
        ).fetchone()["c"]
        tables = conn.execute(
            "SELECT COUNT(*) c FROM sqlite_master WHERE type='table'"
        ).fetchone()["c"]
    return {
        "ok": True,
        "product": PRODUCT,
        "domain": PRODUCT_META["domain"],
        "sub_direction": PRODUCT_META["sub"],
        "skeleton": SKELETON,
        "screens": screens,
        "official_publications": pubs,
        "tables": tables,
        "db": str(DB_PATH),
    }


app.mount("/assets", StaticFiles(directory=str(FRONTEND)), name="assets")


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
