window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["overrides-view"] = {
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
};
