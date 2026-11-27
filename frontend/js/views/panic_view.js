window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["panic-view"] = {
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
};
