window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["publish-view"] = {
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
};
