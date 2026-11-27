# -*- coding: utf-8 -*-
"""组装并落地 18-signboard 母仓。"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def load(name: str):
    path = HERE / name
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def w(rel: str, text: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if text.startswith("\n"):
        text = text[1:]
    path.write_text(text, encoding="utf-8")
    print(f"wrote {rel} ({len(text.splitlines())} lines)")


def main() -> None:
    base = load("_build_signboard.py")
    svc = load("_build_signboard_svc.py")
    biz = load("_build_signboard_biz.py")
    write = load("_build_signboard_write.py")
    front = load("_build_signboard_front.py")

    # root meta from base.main partial — call only the file writers we need
    w("requirements.txt", "fastapi==0.115.6\nuvicorn[standard]==0.32.1\npytest==8.3.4\nhttpx==0.28.1\n")
    w("pytest.ini", "[pytest]\npythonpath = backend\ntestpaths = tests\n")
    w(".gitignore", "data/\n__pycache__/\n.pytest_cache/\n*.pyc\n.venv/\n")
    w(
        "Dockerfile",
        """FROM python:3.12-slim
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
        """name: signboard
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
        """# 楼宇数字标牌编排（signboard）

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

    w("scripts/count_loc.py", base.COUNT_LOC)
    w("backend/__init__.py", '"""signboard backend."""\n')
    w("backend/models.py", base.MODELS)
    w("backend/db.py", base.DB)
    w("backend/auth.py", svc.AUTH)
    w("backend/validators.py", svc.VALIDATORS)
    w("backend/policies.py", svc.POLICIES)
    w("backend/locks.py", svc.LOCKS)
    w("backend/audit_svc.py", svc.AUDIT)
    w("backend/dashboard_svc.py", biz.DASHBOARD)
    w("backend/assets_svc.py", biz.ASSETS)
    w("backend/screens_svc.py", biz.SCREENS)
    w("backend/zones_svc.py", biz.ZONES)
    w("backend/playlists_svc.py", biz.PLAYLISTS)
    w("backend/windows_svc.py", biz.WINDOWS)
    w("backend/publish_svc.py", write.PUBLISH)
    w("backend/panic_svc.py", write.PANIC)
    w("backend/overrides_svc.py", write.OVERRIDES)
    w("backend/evaluate_svc.py", write.EVALUATE)
    w("backend/history_svc.py", write.HISTORY)
    w("backend/layouts_svc.py", write.LAYOUTS)
    w("backend/stubs_svc.py", write.STUBS)
    w("backend/app.py", write.APP)

    for name, body in front.FIXTURES.items():
        w(f"fixtures/{name}", body if body.endswith("\n") else body + "\n")

    w("frontend/index.html", front.INDEX_HTML)
    w("frontend/css/app.css", front.APP_CSS)
    w("frontend/js/api.js", front.API_JS)
    # fixed app.js with component registry
    w(
        "frontend/js/app.js",
        """
const { createApp } = Vue;
const app = createApp({
  data() {
    return {
      token: SB.token,
      username: "admin",
      password: "admin123",
      display: "",
      role: "",
      error: "",
      tab: "dashboard",
      tabs: [
        { id: "dashboard", label: "总览" },
        { id: "zones", label: "分区" },
        { id: "screens", label: "屏幕" },
        { id: "assets", label: "素材" },
        { id: "layouts", label: "布局" },
        { id: "playlists", label: "播放清单" },
        { id: "windows", label: "时段窗" },
        { id: "publish", label: "发布上屏" },
        { id: "panic", label: "紧急撤屏" },
        { id: "overrides", label: "单屏覆盖" },
        { id: "evaluate", label: "在线求值" },
        { id: "history", label: "变更历史" },
        { id: "stubs", label: "空桩桥" },
      ],
    };
  },
  async mounted() {
    if (this.token) {
      try {
        const me = await SB.api("/api/auth/me");
        this.display = me.display;
        this.role = me.role;
      } catch (e) {
        this.logout();
      }
    }
  },
  methods: {
    async login() {
      this.error = "";
      try {
        const data = await SB.api("/api/auth/login", {
          method: "POST",
          body: JSON.stringify({ username: this.username, password: this.password }),
        });
        SB.token = data.token;
        localStorage.setItem("sb_token", data.token);
        this.token = data.token;
        this.display = data.display;
        this.role = data.role;
      } catch (e) {
        this.error = e.message;
      }
    },
    logout() {
      SB.token = "";
      localStorage.removeItem("sb_token");
      this.token = "";
      this.display = "";
      this.role = "";
    },
  },
});
Object.entries(window.SB_VIEWS || {}).forEach(([name, def]) => app.component(name, def));
app.mount("#app");
""",
    )

    # rewrite views to SB_VIEWS registry
    for name, body in front.VIEWS.items():
        fixed = body.replace("app.component(", "window.SB_VIEWS = window.SB_VIEWS || {};\nwindow.SB_VIEWS[")
        # app.component("dashboard-view", { → window.SB_VIEWS["dashboard-view"] = {
        fixed = body
        if 'app.component("' in body:
            import re

            fixed = re.sub(
                r'app\.component\("([^"]+)",\s*\{',
                r'window.SB_VIEWS = window.SB_VIEWS || {};\nwindow.SB_VIEWS["\1"] = {',
                body,
            )
        w(f"frontend/js/views/{name}", fixed)

    w("tests/test_smoke.py", front.TEST_SMOKE)
    w("tests/test_paths.py", front.TEST_PATHS)
    print("OK", ROOT)


if __name__ == "__main__":
    main()
