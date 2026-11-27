"""路径与模块存在性。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
FIXTURES = ROOT / "fixtures"

REQUIRED_BACKEND = [
    "app.py",
    "db.py",
    "models.py",
    "auth.py",
    "assets_svc.py",
    "screens_svc.py",
    "zones_svc.py",
    "playlists_svc.py",
    "windows_svc.py",
    "publish_svc.py",
    "panic_svc.py",
    "overrides_svc.py",
    "evaluate_svc.py",
    "history_svc.py",
    "layouts_svc.py",
    "stubs_svc.py",
    "locks.py",
    "audit_svc.py",
    "policies.py",
    "validators.py",
    "dashboard_svc.py",
]

REQUIRED_VIEWS = [
    "dashboard_view.js",
    "zones_view.js",
    "screens_view.js",
    "assets_view.js",
    "playlists_view.js",
    "windows_view.js",
    "publish_view.js",
    "panic_view.js",
    "overrides_view.js",
    "evaluate_view.js",
    "history_view.js",
    "layouts_view.js",
    "stubs_view.js",
]

REQUIRED_FIXTURES = [
    "zones.json",
    "screens.json",
    "assets.json",
    "layouts.json",
    "playlists.json",
    "playlist_items.json",
    "time_windows.json",
    "publications.json",
    "change_history.json",
]


def test_backend_modules_exist():
    for name in REQUIRED_BACKEND:
        assert (BACKEND / name).exists(), name


def test_frontend_views_exist():
    for name in REQUIRED_VIEWS:
        assert (FRONTEND / "js" / "views" / name).exists(), name


def test_fixtures_exist():
    for name in REQUIRED_FIXTURES:
        assert (FIXTURES / name).exists(), name


def test_docker_files():
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "docker-compose.yml").exists()
