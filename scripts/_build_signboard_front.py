# -*- coding: utf-8 -*-
"""signboard 前端与夹具、测试常量。"""
from __future__ import annotations

import json

FIXTURES = {
    "zones.json": json.dumps(
        [
            {"code": "lobby_a", "title": "A座大堂", "zone_type": "lobby", "risk_level": 3, "floor_label": "1F"},
            {"code": "lift_b3", "title": "B座电梯厅3层", "zone_type": "elevator", "risk_level": 2, "floor_label": "3F"},
            {"code": "corr_c2", "title": "C座走廊2层", "zone_type": "corridor", "risk_level": 2, "floor_label": "2F"},
            {"code": "meet_d1", "title": "D座多功能厅", "zone_type": "meeting", "risk_level": 3, "floor_label": "1F"},
            {"code": "yard_east", "title": "东侧室外立柱屏", "zone_type": "outdoor", "risk_level": 4, "floor_label": "G"},
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "screens.json": json.dumps(
        [
            {"code": "scr_lobby_main", "title": "大堂主屏", "zone_code": "lobby_a", "resolution": "1920x1080", "status": "online", "orientation": "landscape"},
            {"code": "scr_lobby_side", "title": "大堂侧屏", "zone_code": "lobby_a", "resolution": "1080x1920", "status": "online", "orientation": "portrait"},
            {"code": "scr_lift_b3", "title": "电梯厅竖屏", "zone_code": "lift_b3", "resolution": "1080x1920", "status": "online", "orientation": "portrait"},
            {"code": "scr_corr_c2", "title": "走廊横条", "zone_code": "corr_c2", "resolution": "1920x1080", "status": "offline"},
            {"code": "scr_meet_d1", "title": "多功能厅导览", "zone_code": "meet_d1", "resolution": "1920x1080", "status": "online"},
            {"code": "scr_yard_e1", "title": "室外立柱", "zone_code": "yard_east", "resolution": "1080x1920", "status": "maintenance", "note": "面板检修"},
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "assets.json": json.dumps(
        [
            {"code": "img_welcome", "title": "欢迎图", "kind": "image", "duration_sec": 12, "resolution": "1920x1080", "status": "ready", "owner": "admin", "checksum": "a1"},
            {"code": "vid_safety", "title": "安全须知视频", "kind": "video", "duration_sec": 45, "resolution": "1920x1080", "status": "ready", "owner": "writer", "checksum": "b2"},
            {"code": "html_menu", "title": "今日菜单页", "kind": "html", "duration_sec": 20, "resolution": "1080x1920", "status": "ready", "owner": "writer", "checksum": "c3"},
            {"code": "tick_notice", "title": "滚动公告", "kind": "ticker", "duration_sec": 8, "resolution": "1920x1080", "status": "ready", "owner": "admin", "checksum": "d4"},
            {"code": "img_event", "title": "活动海报", "kind": "image", "duration_sec": 15, "resolution": "1080x1920", "status": "ready", "owner": "writer", "checksum": "e5"},
            {"code": "img_draft", "title": "未审海报", "kind": "image", "duration_sec": 10, "resolution": "1920x1080", "status": "draft", "owner": "writer", "checksum": "f6"},
            {"code": "vid_brand", "title": "品牌片", "kind": "video", "duration_sec": 60, "resolution": "3840x2160", "status": "ready", "owner": "admin", "checksum": "g7"},
            {"code": "html_wayfind", "title": "寻路页", "kind": "html", "duration_sec": 25, "resolution": "1920x1080", "status": "ready", "owner": "admin", "checksum": "h8"},
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "layouts.json": json.dumps(
        [
            {"code": "lay_full", "title": "全屏单槽", "slots": [{"name": "main", "x": 0, "y": 0, "w": 100, "h": 100}]},
            {"code": "lay_split", "title": "上下分栏", "slots": [{"name": "top", "x": 0, "y": 0, "w": 100, "h": 70}, {"name": "ticker", "x": 0, "y": 70, "w": 100, "h": 30}]},
            {"code": "lay_lbar", "title": "左栏导览", "slots": [{"name": "side", "x": 0, "y": 0, "w": 30, "h": 100}, {"name": "main", "x": 30, "y": 0, "w": 70, "h": 100}]},
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "playlists.json": json.dumps(
        [
            {"code": "pl_lobby_day", "title": "大堂日间清单", "status": "ready", "transition": "fade", "loop": True, "owner": "admin"},
            {"code": "pl_lift_loop", "title": "电梯厅循环", "status": "ready", "transition": "cut", "loop": True, "owner": "writer"},
            {"code": "pl_event_temp", "title": "活动临时清单", "status": "draft", "transition": "slide_left", "loop": True, "owner": "writer"},
            {"code": "pl_meet_guide", "title": "会议导览清单", "status": "ready", "transition": "fade", "loop": False, "owner": "admin"},
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "playlist_items.json": json.dumps(
        [
            {"playlist_code": "pl_lobby_day", "asset_code": "img_welcome", "seq": 1, "dwell_sec": 12},
            {"playlist_code": "pl_lobby_day", "asset_code": "vid_safety", "seq": 2, "dwell_sec": 45},
            {"playlist_code": "pl_lobby_day", "asset_code": "tick_notice", "seq": 3, "dwell_sec": 8},
            {"playlist_code": "pl_lift_loop", "asset_code": "html_menu", "seq": 1, "dwell_sec": 20},
            {"playlist_code": "pl_lift_loop", "asset_code": "img_event", "seq": 2, "dwell_sec": 15},
            {"playlist_code": "pl_meet_guide", "asset_code": "html_wayfind", "seq": 1, "dwell_sec": 25},
            {"playlist_code": "pl_meet_guide", "asset_code": "img_welcome", "seq": 2, "dwell_sec": 12},
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "time_windows.json": json.dumps(
        [
            {"code": "win_workday", "title": "工作日日间", "start_hm": "08:00", "end_hm": "19:00", "weekdays": "1,2,3,4,5", "status": "open"},
            {"code": "win_evening", "title": "晚间延展", "start_hm": "19:00", "end_hm": "22:00", "weekdays": "1,2,3,4,5", "status": "open"},
            {"code": "win_weekend", "title": "周末开放", "start_hm": "10:00", "end_hm": "18:00", "weekdays": "6,7", "status": "open"},
            {"code": "win_closed", "title": "已关闭窗", "start_hm": "00:00", "end_hm": "06:00", "weekdays": "1,2,3,4,5", "status": "closed", "note": "停用"},
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "publications.json": json.dumps(
        [
            {
                "screen_code": "scr_lobby_main",
                "playlist_code": "pl_lobby_day",
                "window_code": "win_workday",
                "layout_code": "lay_split",
                "version": 3,
                "summary": "大堂日间正式发布",
                "status": "published",
                "published_by": "admin",
            },
            {
                "screen_code": "scr_lift_b3",
                "playlist_code": "pl_lift_loop",
                "window_code": "win_workday",
                "layout_code": "lay_full",
                "version": 2,
                "summary": "电梯厅循环正式发布",
                "status": "published",
                "published_by": "writer",
            },
            {
                "screen_code": "scr_meet_d1",
                "playlist_code": "pl_meet_guide",
                "window_code": "win_weekend",
                "layout_code": "lay_lbar",
                "version": 1,
                "summary": "会议导览周末发布",
                "status": "published",
                "published_by": "admin",
            },
        ],
        ensure_ascii=False,
        indent=2,
    ),
    "change_history.json": json.dumps(
        [
            {"entity_kind": "publication", "entity_id": 1, "action": "publish_official", "detail": "大堂日间正式发布", "actor": "admin", "age_hours": 5},
            {"entity_kind": "publication", "entity_id": 2, "action": "publish_official", "detail": "电梯厅循环正式发布", "actor": "writer", "age_hours": 4},
            {"entity_kind": "asset", "entity_id": 1, "action": "create", "detail": "创建欢迎图", "actor": "admin", "age_hours": 48},
            {"entity_kind": "playlist", "entity_id": 1, "action": "patch", "detail": "清单状态=ready", "actor": "admin", "age_hours": 20},
            {"entity_kind": "window", "entity_id": 1, "action": "create", "detail": "创建工作日日间", "actor": "admin", "age_hours": 72},
        ],
        ensure_ascii=False,
        indent=2,
    ),
}

INDEX_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>楼宇数字标牌编排</title>
  <link rel="stylesheet" href="/assets/css/app.css" />
  <script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
</head>
<body>
  <div id="app">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">SB</div>
        <div>
          <div class="brand-name">楼宇数字标牌编排</div>
          <div class="brand-sub">应用开发 · 全栈 · 发布须版本落库</div>
        </div>
      </div>
      <div class="top-actions" v-if="token">
        <span class="who">{{ display }}（{{ role }}）</span>
        <button class="ghost" @click="logout">退出</button>
      </div>
    </header>

    <section v-if="!token" class="login-panel">
      <h1>登录编排台</h1>
      <p class="hint">演示账号 admin / writer / viewer</p>
      <label>用户名<input v-model="username" /></label>
      <label>密码<input type="password" v-model="password" @keyup.enter="login" /></label>
      <button class="primary" @click="login">进入</button>
      <p class="err" v-if="error">{{ error }}</p>
    </section>

    <div v-else class="shell">
      <nav class="rail">
        <button v-for="t in tabs" :key="t.id" :class="{on: tab===t.id}" @click="tab=t.id">{{ t.label }}</button>
      </nav>
      <main class="stage">
        <dashboard-view v-if="tab==='dashboard'" />
        <zones-view v-else-if="tab==='zones'" />
        <screens-view v-else-if="tab==='screens'" />
        <assets-view v-else-if="tab==='assets'" />
        <playlists-view v-else-if="tab==='playlists'" />
        <windows-view v-else-if="tab==='windows'" />
        <publish-view v-else-if="tab==='publish'" />
        <panic-view v-else-if="tab==='panic'" />
        <overrides-view v-else-if="tab==='overrides'" />
        <evaluate-view v-else-if="tab==='evaluate'" />
        <history-view v-else-if="tab==='history'" />
        <layouts-view v-else-if="tab==='layouts'" />
        <stubs-view v-else-if="tab==='stubs'" />
      </main>
    </div>
  </div>
  <script src="/assets/js/api.js"></script>
  <script src="/assets/js/views/dashboard_view.js"></script>
  <script src="/assets/js/views/zones_view.js"></script>
  <script src="/assets/js/views/screens_view.js"></script>
  <script src="/assets/js/views/assets_view.js"></script>
  <script src="/assets/js/views/playlists_view.js"></script>
  <script src="/assets/js/views/windows_view.js"></script>
  <script src="/assets/js/views/publish_view.js"></script>
  <script src="/assets/js/views/panic_view.js"></script>
  <script src="/assets/js/views/overrides_view.js"></script>
  <script src="/assets/js/views/evaluate_view.js"></script>
  <script src="/assets/js/views/history_view.js"></script>
  <script src="/assets/js/views/layouts_view.js"></script>
  <script src="/assets/js/views/stubs_view.js"></script>
  <script src="/assets/js/app.js"></script>
</body>
</html>
'''

APP_CSS = r'''
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&family=Space+Grotesk:wght@500;700&display=swap");
:root {
  --bg: #0f1b2d;
  --panel: #16263d;
  --ink: #e8eef7;
  --muted: #8fa3bf;
  --accent: #f0a202;
  --accent2: #3ecf8e;
  --danger: #ff6b6b;
  --line: rgba(255,255,255,.08);
  --rail: #0b1422;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  font-family: "IBM Plex Sans", sans-serif;
  color: var(--ink);
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(240,162,2,.18), transparent 55%),
    radial-gradient(900px 500px at 90% 0%, rgba(62,207,142,.12), transparent 50%),
    linear-gradient(180deg, #0c1626, #13233a 40%, #0f1b2d);
}
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 28px; border-bottom: 1px solid var(--line);
  backdrop-filter: blur(8px);
}
.brand { display: flex; gap: 14px; align-items: center; }
.brand-mark {
  width: 42px; height: 42px; border-radius: 10px;
  display: grid; place-items: center;
  font-family: "Space Grotesk", sans-serif; font-weight: 700;
  background: linear-gradient(135deg, var(--accent), #ffcf5c);
  color: #1a1200;
}
.brand-name { font-family: "Space Grotesk", sans-serif; font-size: 20px; font-weight: 700; }
.brand-sub { color: var(--muted); font-size: 12px; margin-top: 2px; }
.who { color: var(--muted); margin-right: 12px; }
.login-panel {
  width: min(420px, 92vw); margin: 10vh auto; padding: 28px;
  background: var(--panel); border: 1px solid var(--line); border-radius: 16px;
  display: grid; gap: 12px;
}
.login-panel h1 { margin: 0; font-family: "Space Grotesk", sans-serif; }
.hint, .err { color: var(--muted); margin: 0; }
.err { color: var(--danger); }
label { display: grid; gap: 6px; font-size: 13px; color: var(--muted); }
input, select, textarea {
  background: #0d1828; border: 1px solid var(--line); color: var(--ink);
  border-radius: 10px; padding: 10px 12px; font: inherit;
}
button {
  border: 0; border-radius: 10px; padding: 10px 14px; cursor: pointer; font: inherit;
}
button.primary { background: var(--accent); color: #1a1200; font-weight: 700; }
button.ghost { background: transparent; color: var(--ink); border: 1px solid var(--line); }
button.danger { background: var(--danger); color: #fff; font-weight: 700; }
.shell { display: grid; grid-template-columns: 200px 1fr; min-height: calc(100vh - 74px); }
.rail {
  background: var(--rail); border-right: 1px solid var(--line);
  padding: 16px 10px; display: grid; gap: 6px; align-content: start;
}
.rail button {
  text-align: left; background: transparent; color: var(--muted); padding: 10px 12px;
}
.rail button.on { background: rgba(240,162,2,.14); color: var(--accent); font-weight: 600; }
.stage { padding: 22px 26px 40px; }
.panel {
  background: rgba(22,38,61,.88); border: 1px solid var(--line);
  border-radius: 16px; padding: 18px 18px 8px; margin-bottom: 16px;
}
.panel h2 { margin: 0 0 8px; font-family: "Space Grotesk", sans-serif; font-size: 18px; }
.panel p.lead { color: var(--muted); margin: 0 0 14px; font-size: 13px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit,minmax(140px,1fr)); gap: 12px; }
.stat {
  background: #0d1828; border-radius: 12px; padding: 14px; border: 1px solid var(--line);
}
.stat b { display: block; font-size: 22px; font-family: "Space Grotesk", sans-serif; }
.stat span { color: var(--muted); font-size: 12px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { color: var(--muted); font-weight: 600; }
.row-form { display: grid; grid-template-columns: repeat(auto-fit,minmax(160px,1fr)); gap: 10px; margin-bottom: 12px; }
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px;
  background: rgba(62,207,142,.15); color: var(--accent2);
}
.badge.warn { background: rgba(240,162,2,.15); color: var(--accent); }
.badge.bad { background: rgba(255,107,107,.15); color: var(--danger); }
.two-col { display: grid; grid-template-columns: 1.2fr .8fr; gap: 16px; }
@media (max-width: 960px) {
  .shell { grid-template-columns: 1fr; }
  .rail { grid-auto-flow: column; overflow-x: auto; }
  .two-col { grid-template-columns: 1fr; }
}
'''

API_JS = r'''
window.SB = window.SB || {};
SB.token = localStorage.getItem("sb_token") || "";
SB.api = async function(path, opts = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
  if (SB.token) headers.Authorization = "Bearer " + SB.token;
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { data = { raw: text }; }
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || res.statusText || "请求失败";
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
};
'''

APP_JS = r'''
const { createApp } = Vue;
createApp({
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
}).mount("#app");
'''


def _view(title, lead, load_path, columns, form_html="", extra_methods=""):
    cols_js = ",\n          ".join([f"{{ key: '{k}', label: '{lab}' }}" for k, lab in columns])
    return f'''
window.SB = window.SB || {{}};
SB.components = SB.components || {{}};
const {title.replace("-", "").title().replace(" ", "")}Comp = {{
  template: `
  <div>
    <div class="panel">
      <h2>{title}</h2>
      <p class="lead">{lead}</p>
      {form_html}
      <p class="err" v-if="error">{{{{ error }}}}</p>
    </div>
    <div class="panel">
      <table>
        <thead><tr>
          <th v-for="c in columns" :key="c.key">{{{{ c.label }}}}</th>
        </tr></thead>
        <tbody>
          <tr v-for="row in items" :key="row.id || JSON.stringify(row)">
            <td v-for="c in columns" :key="c.key">{{{{ format(row, c.key) }}}}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`,
  data() {{
    return {{ items: [], error: "", form: {{}}, columns: [
          {cols_js}
    ] }};
  }},
  async mounted() {{ await this.reload(); }},
  methods: {{
    format(row, key) {{
      const v = row[key];
      if (v === null || v === undefined) return "—";
      if (typeof v === "object") return JSON.stringify(v);
      return v;
    }},
    async reload() {{
      this.error = "";
      try {{
        const data = await SB.api("{load_path}");
        this.items = data.items || data.events || [];
      }} catch (e) {{ this.error = e.message; }}
    }},
    {extra_methods}
  }}
}};
'''


# Simpler handcrafted views for key pages
VIEWS = {}

VIEWS["dashboard_view.js"] = r'''
app.component("dashboard-view", {
  template: `
  <div class="panel">
    <h2>总览</h2>
    <p class="lead">{{ meta.skeleton || "加载中…" }}</p>
    <div class="stats">
      <div class="stat" v-for="s in cards" :key="s.k"><b>{{ s.v }}</b><span>{{ s.l }}</span></div>
    </div>
  </div>`,
  data() { return { meta: {}, cards: [] }; },
  async mounted() {
    const d = await SB.api("/api/dashboard");
    this.meta = d;
    this.cards = [
      { k: "screens", l: "屏幕总数", v: d.screens },
      { k: "online", l: "在线屏幕", v: d.online_screens },
      { k: "assets", l: "可播素材", v: d.ready_assets },
      { k: "pubs", l: "正式发布", v: d.official_publications },
      { k: "shadows", l: "待升正影子", v: d.open_shadows },
      { k: "ov", l: "生效覆盖", v: d.active_overrides },
    ];
  }
});
'''

VIEWS["zones_view.js"] = r'''
app.component("zones-view", {
  template: `
  <div>
    <div class="panel">
      <h2>楼宇分区</h2>
      <p class="lead">分区约束风险等级与可发布屏幕范围。</p>
      <div class="row-form">
        <input v-model="form.code" placeholder="编码" />
        <input v-model="form.title" placeholder="标题" />
        <select v-model="form.zone_type">
          <option value="lobby">大堂</option>
          <option value="elevator">电梯厅</option>
          <option value="corridor">走廊</option>
          <option value="meeting">会议室</option>
          <option value="outdoor">室外</option>
        </select>
        <input v-model.number="form.risk_level" type="number" min="1" max="5" placeholder="风险" />
        <button class="primary" @click="create">新建分区</button>
      </div>
      <p class="err" v-if="error">{{ error }}</p>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>编码</th><th>标题</th><th>类型</th><th>风险</th><th>楼层</th></tr></thead>
        <tbody>
          <tr v-for="z in items" :key="z.id">
            <td>{{ z.code }}</td><td>{{ z.title }}</td><td>{{ z.zone_type_label }}</td>
            <td>{{ z.risk_label }}</td><td>{{ z.floor_label || "—" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`,
  data() { return { items: [], error: "", form: { code: "", title: "", zone_type: "lobby", risk_level: 2 } }; },
  async mounted() { await this.reload(); },
  methods: {
    async reload() { this.items = (await SB.api("/api/zones")).items; },
    async create() {
      this.error = "";
      try { await SB.api("/api/zones", { method: "POST", body: JSON.stringify(this.form) }); await this.reload(); }
      catch (e) { this.error = e.message; }
    }
  }
});
'''

VIEWS["screens_view.js"] = r'''
app.component("screens-view", {
  template: `
  <div class="panel">
    <h2>屏幕台账</h2>
    <p class="lead">物理终端绑定分区、分辨率与在线状态。</p>
    <table>
      <thead><tr><th>编码</th><th>标题</th><th>分区</th><th>分辨率</th><th>状态</th><th>风险</th></tr></thead>
      <tbody>
        <tr v-for="s in items" :key="s.id">
          <td>{{ s.code }}</td><td>{{ s.title }}</td><td>{{ s.zone_title }}</td>
          <td>{{ s.resolution }}</td>
          <td><span class="badge" :class="s.status==='online'?'':(s.status==='maintenance'?'bad':'warn')">{{ s.status_label }}</span></td>
          <td>{{ s.risk_level }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [] }; },
  async mounted() { this.items = (await SB.api("/api/screens")).items; }
});
'''

VIEWS["assets_view.js"] = r'''
app.component("assets-view", {
  template: `
  <div>
    <div class="panel">
      <h2>素材台账</h2>
      <p class="lead">图片 / 视频 / 网页页 / 滚动条，可播后才能进清单。</p>
      <div class="row-form">
        <input v-model="form.code" placeholder="编码" />
        <input v-model="form.title" placeholder="标题" />
        <select v-model="form.kind"><option>image</option><option>video</option><option>html</option><option>ticker</option></select>
        <input v-model="form.resolution" placeholder="分辨率" />
        <select v-model="form.status"><option>draft</option><option>ready</option></select>
        <button class="primary" @click="create">登记素材</button>
      </div>
      <p class="err" v-if="error">{{ error }}</p>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>编码</th><th>标题</th><th>种类</th><th>时长</th><th>分辨率</th><th>状态</th></tr></thead>
        <tbody>
          <tr v-for="a in items" :key="a.id">
            <td>{{ a.code }}</td><td>{{ a.title }}</td><td>{{ a.kind_label }}</td>
            <td>{{ a.duration_sec }}s</td><td>{{ a.resolution }}</td><td>{{ a.status_label }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`,
  data() { return { items: [], error: "", form: { code: "", title: "", kind: "image", resolution: "1920x1080", status: "draft", duration_sec: 12 } }; },
  async mounted() { await this.reload(); },
  methods: {
    async reload() { this.items = (await SB.api("/api/assets")).items; },
    async create() {
      this.error = "";
      try { await SB.api("/api/assets", { method: "POST", body: JSON.stringify(this.form) }); await this.reload(); }
      catch (e) { this.error = e.message; }
    }
  }
});
'''

VIEWS["playlists_view.js"] = r'''
app.component("playlists-view", {
  template: `
  <div class="panel">
    <h2>播放清单</h2>
    <p class="lead">有序素材序列；置为可播后才能发布上屏。</p>
    <table>
      <thead><tr><th>编码</th><th>标题</th><th>状态</th><th>过渡</th><th>条目数</th><th>负责人</th></tr></thead>
      <tbody>
        <tr v-for="p in items" :key="p.id">
          <td>{{ p.code }}</td><td>{{ p.title }}</td><td>{{ p.status }}</td>
          <td>{{ p.transition }}</td><td>{{ p.item_count }}</td><td>{{ p.owner }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [] }; },
  async mounted() { this.items = (await SB.api("/api/playlists")).items; }
});
'''

VIEWS["windows_view.js"] = r'''
app.component("windows-view", {
  template: `
  <div class="panel">
    <h2>时段窗</h2>
    <p class="lead">限制清单在哪些钟点与星期可上屏。</p>
    <table>
      <thead><tr><th>编码</th><th>标题</th><th>起止</th><th>星期</th><th>状态</th></tr></thead>
      <tbody>
        <tr v-for="w in items" :key="w.id">
          <td>{{ w.code }}</td><td>{{ w.title }}</td>
          <td>{{ w.start_hm }} — {{ w.end_hm }}</td><td>{{ w.weekdays }}</td><td>{{ w.status }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [] }; },
  async mounted() { this.items = (await SB.api("/api/windows")).items; }
});
'''

VIEWS["publish_view.js"] = r'''
app.component("publish-view", {
  template: `
  <div class="two-col">
    <div>
      <div class="panel">
        <h2>发布上屏</h2>
        <p class="lead">甲：正式事务直写；乙：影子草案再升正。两边不得混用。</p>
        <div class="row-form">
          <input v-model.number="form.screen_id" type="number" placeholder="屏幕ID" />
          <input v-model.number="form.playlist_id" type="number" placeholder="清单ID" />
          <input v-model.number="form.window_id" type="number" placeholder="时段ID" />
          <input v-model="form.summary" placeholder="摘要" />
        </div>
        <div class="row-form">
          <button class="primary" @click="official">正式发布（甲）</button>
          <button class="ghost" @click="shadow">写影子草案（乙）</button>
          <input v-model.number="shadowId" type="number" placeholder="影子ID" />
          <button class="primary" @click="promote">升正影子</button>
        </div>
        <p class="err" v-if="error">{{ error }}</p>
        <p v-if="msg">{{ msg }}</p>
      </div>
      <div class="panel">
        <h3>正式发布</h3>
        <table>
          <thead><tr><th>ID</th><th>屏幕</th><th>清单</th><th>时段</th><th>版本</th><th>摘要</th></tr></thead>
          <tbody>
            <tr v-for="p in official" :key="p.id">
              <td>{{ p.id }}</td><td>{{ p.screen_code }}</td><td>{{ p.playlist_code }}</td>
              <td>{{ p.window_code }}</td><td>v{{ p.version }}</td><td>{{ p.summary }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="panel">
      <h3>影子草案</h3>
      <table>
        <thead><tr><th>ID</th><th>屏幕</th><th>状态</th><th>摘要</th></tr></thead>
        <tbody>
          <tr v-for="s in shadows" :key="s.id">
            <td>{{ s.id }}</td><td>{{ s.screen_code }}</td><td>{{ s.status }}</td><td>{{ s.summary }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`,
  data() {
    return {
      form: { screen_id: 1, playlist_id: 1, window_id: 1, summary: "编排发布" },
      shadowId: null, official: [], shadows: [], error: "", msg: ""
    };
  },
  async mounted() { await this.reload(); },
  methods: {
    async reload() {
      this.official = (await SB.api("/api/publish/official")).items;
      this.shadows = (await SB.api("/api/publish/shadows")).items;
    },
    async official() {
      this.error = ""; this.msg = "";
      try {
        const r = await SB.api("/api/publish/official", { method: "POST", body: JSON.stringify(this.form) });
        this.msg = "正式发布完成 version=" + r.version; await this.reload();
      } catch (e) { this.error = e.message; }
    },
    async shadow() {
      this.error = ""; this.msg = "";
      try {
        const r = await SB.api("/api/publish/shadow", { method: "POST", body: JSON.stringify(this.form) });
        this.msg = "影子已写 id=" + r.id; this.shadowId = r.id; await this.reload();
      } catch (e) { this.error = e.message; }
    },
    async promote() {
      this.error = ""; this.msg = "";
      try {
        const r = await SB.api("/api/publish/shadow/" + this.shadowId + "/promote", { method: "POST", body: "{}" });
        this.msg = "升正完成 version=" + r.version; await this.reload();
      } catch (e) { this.error = e.message; }
    }
  }
});
'''

VIEWS["panic_view.js"] = r'''
app.component("panic-view", {
  template: `
  <div class="panel">
    <h2>紧急撤屏</h2>
    <p class="lead">清空正式发布；甲直写事件，乙影子升正。</p>
    <div class="row-form">
      <input v-model.number="screen_id" type="number" placeholder="屏幕ID" />
      <input v-model="reason" placeholder="原因" />
      <button class="danger" @click="official">正式撤屏</button>
      <button class="ghost" @click="shadow">影子撤屏</button>
      <input v-model.number="shadowId" type="number" placeholder="影子ID" />
      <button class="primary" @click="promote">升正</button>
    </div>
    <p class="err" v-if="error">{{ error }}</p>
    <table>
      <thead><tr><th>ID</th><th>屏幕</th><th>原因</th><th>操作者</th></tr></thead>
      <tbody>
        <tr v-for="e in items" :key="e.id"><td>{{ e.id }}</td><td>{{ e.screen_code }}</td><td>{{ e.reason }}</td><td>{{ e.created_by }}</td></tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [], screen_id: 1, reason: "内容异常", shadowId: null, error: "" }; },
  async mounted() { this.items = (await SB.api("/api/panic/events")).items; },
  methods: {
    async official() {
      try {
        await SB.api("/api/panic/official", { method: "POST", body: JSON.stringify({ screen_id: this.screen_id, reason: this.reason }) });
        this.items = (await SB.api("/api/panic/events")).items;
      } catch (e) { this.error = e.message; }
    },
    async shadow() {
      try {
        const r = await SB.api("/api/panic/shadow", { method: "POST", body: JSON.stringify({ screen_id: this.screen_id, reason: this.reason }) });
        this.shadowId = r.id;
      } catch (e) { this.error = e.message; }
    },
    async promote() {
      try {
        await SB.api("/api/panic/shadow/" + this.shadowId + "/promote", { method: "POST", body: "{}" });
        this.items = (await SB.api("/api/panic/events")).items;
      } catch (e) { this.error = e.message; }
    }
  }
});
'''

VIEWS["overrides_view.js"] = r'''
app.component("overrides-view", {
  template: `
  <div class="panel">
    <h2>单屏覆盖</h2>
    <p class="lead">临时强制清单 / 空屏 / 单素材，求值优先于正式发布。</p>
    <div class="row-form">
      <input v-model.number="form.screen_id" type="number" placeholder="屏幕ID" />
      <select v-model="form.effect">
        <option value="force_blank">强制空屏</option>
        <option value="force_playlist">强制清单</option>
        <option value="force_asset">强制单素材</option>
      </select>
      <input v-model.number="form.playlist_id" type="number" placeholder="清单ID(可选)" />
      <input v-model.number="form.asset_id" type="number" placeholder="素材ID(可选)" />
      <button class="primary" @click="create">正式覆盖</button>
    </div>
    <p class="err" v-if="error">{{ error }}</p>
    <table>
      <thead><tr><th>ID</th><th>屏幕</th><th>效果</th><th>生效</th><th>备注</th></tr></thead>
      <tbody>
        <tr v-for="o in items" :key="o.id">
          <td>{{ o.id }}</td><td>{{ o.screen_code }}</td><td>{{ o.effect }}</td>
          <td>{{ o.active ? "是" : "否" }}</td><td>{{ o.note || "—" }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [], error: "", form: { screen_id: 1, effect: "force_blank", playlist_id: null, asset_id: null, note: "" } }; },
  async mounted() { this.items = (await SB.api("/api/overrides")).items; },
  methods: {
    async create() {
      this.error = "";
      const body = { ...this.form };
      if (body.effect === "force_blank") { body.playlist_id = null; body.asset_id = null; }
      try {
        await SB.api("/api/overrides/official", { method: "POST", body: JSON.stringify(body) });
        this.items = (await SB.api("/api/overrides")).items;
      } catch (e) { this.error = e.message; }
    }
  }
});
'''

VIEWS["evaluate_view.js"] = r'''
app.component("evaluate-view", {
  template: `
  <div class="panel">
    <h2>在线求值</h2>
    <p class="lead">给定屏幕与时刻，计算应播内容（覆盖优先）。</p>
    <div class="row-form">
      <input v-model.number="screen_id" type="number" placeholder="屏幕ID" />
      <input v-model="now_hm" placeholder="HH:MM" />
      <input v-model="weekday" placeholder="星期1-7" />
      <button class="primary" @click="run">求值</button>
    </div>
    <pre style="white-space:pre-wrap;background:#0d1828;padding:12px;border-radius:10px;">{{ resultText }}</pre>
    <p class="err" v-if="error">{{ error }}</p>
  </div>`,
  data() { return { screen_id: 1, now_hm: "10:30", weekday: "1", resultText: "", error: "" }; },
  methods: {
    async run() {
      this.error = "";
      try {
        const r = await SB.api("/api/evaluate/screen", {
          method: "POST",
          body: JSON.stringify({ screen_id: this.screen_id, now_hm: this.now_hm, weekday: this.weekday })
        });
        this.resultText = JSON.stringify(r, null, 2);
      } catch (e) { this.error = e.message; }
    }
  }
});
'''

VIEWS["history_view.js"] = r'''
app.component("history-view", {
  template: `
  <div class="panel">
    <h2>变更历史</h2>
    <p class="lead">发布、撤屏、覆盖与台账变更同源可追溯。</p>
    <table>
      <thead><tr><th>ID</th><th>实体</th><th>动作</th><th>详情</th><th>操作者</th></tr></thead>
      <tbody>
        <tr v-for="h in items" :key="h.id">
          <td>{{ h.id }}</td><td>{{ h.entity_kind }}#{{ h.entity_id }}</td>
          <td>{{ h.action }}</td><td>{{ h.detail }}</td><td>{{ h.actor }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [] }; },
  async mounted() { this.items = (await SB.api("/api/history")).items; }
});
'''

VIEWS["layouts_view.js"] = r'''
app.component("layouts-view", {
  template: `
  <div class="panel">
    <h2>屏幕布局</h2>
    <p class="lead">多区画布槽位，发布时可绑定。</p>
    <table>
      <thead><tr><th>编码</th><th>标题</th><th>槽位数</th><th>备注</th></tr></thead>
      <tbody>
        <tr v-for="l in items" :key="l.id">
          <td>{{ l.code }}</td><td>{{ l.title }}</td>
          <td>{{ (l.slots || []).length }}</td><td>{{ l.note || "—" }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [] }; },
  async mounted() { this.items = (await SB.api("/api/layouts")).items; }
});
'''

VIEWS["stubs_view.js"] = r'''
app.component("stubs-view", {
  template: `
  <div class="panel">
    <h2>空桩桥</h2>
    <p class="lead">题面可点名的未实现桥接，固定返回 501。</p>
    <div class="row-form">
      <button class="ghost" @click="call('remote_push')">试调远程推屏</button>
      <button class="ghost" @click="call('media_bridge')">试调媒资桥</button>
    </div>
    <pre style="white-space:pre-wrap;background:#0d1828;padding:12px;border-radius:10px;">{{ out }}</pre>
    <table>
      <thead><tr><th>键</th><th>标题</th><th>说明</th><th>状态</th></tr></thead>
      <tbody>
        <tr v-for="s in items" :key="s.key">
          <td>{{ s.key }}</td><td>{{ s.title }}</td><td>{{ s.desc }}</td><td>{{ s.status }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [], out: "" }; },
  async mounted() { this.items = (await SB.api("/api/stubs")).items; },
  methods: {
    async call(name) {
      try {
        await SB.api("/api/stubs/" + name, { method: "POST", body: "{}" });
      } catch (e) {
        this.out = e.message;
        // 501 also throws via api helper if detail string; show raw attempt
        try {
          const res = await fetch("/api/stubs/" + name, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: "Bearer " + SB.token },
            body: "{}"
          });
          this.out = await res.text();
        } catch (e2) { this.out = String(e2); }
      }
    }
  }
});
'''

TEST_SMOKE = r'''
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
'''

TEST_PATHS = r'''
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
'''
