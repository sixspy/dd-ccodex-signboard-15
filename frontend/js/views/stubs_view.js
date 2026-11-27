window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["stubs-view"] = {
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
};
