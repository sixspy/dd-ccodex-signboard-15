const { createApp } = Vue;

const app = createApp({
  template: `
  <div>
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
        <button class="ghost" type="button" @click="logout">退出</button>
      </div>
    </header>

    <section v-if="!token" class="login-panel">
      <h1>登录编排台</h1>
      <p class="hint">演示账号 admin / writer / viewer</p>
      <label>用户名<input v-model="username" autocomplete="username" /></label>
      <label>密码<input type="password" v-model="password" autocomplete="current-password" @keyup.enter="login" /></label>
      <button class="primary" type="button" @click="login">进入</button>
      <p class="err" v-if="error">{{ error }}</p>
    </section>

    <div v-else class="shell">
      <nav class="rail">
        <button
          v-for="t in tabs"
          :key="t.id"
          type="button"
          :class="{ on: tab === t.id }"
          @click="tab = t.id"
        >{{ t.label }}</button>
      </nav>
      <main class="stage">
        <dashboard-view v-if="tab === 'dashboard'" />
        <zones-view v-else-if="tab === 'zones'" />
        <screens-view v-else-if="tab === 'screens'" />
        <assets-view v-else-if="tab === 'assets'" />
        <playlists-view v-else-if="tab === 'playlists'" />
        <windows-view v-else-if="tab === 'windows'" />
        <publish-view v-else-if="tab === 'publish'" />
        <panic-view v-else-if="tab === 'panic'" />
        <overrides-view v-else-if="tab === 'overrides'" />
        <evaluate-view v-else-if="tab === 'evaluate'" />
        <history-view v-else-if="tab === 'history'" />
        <layouts-view v-else-if="tab === 'layouts'" />
        <stubs-view v-else-if="tab === 'stubs'" />
      </main>
    </div>
  </div>
  `,
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
