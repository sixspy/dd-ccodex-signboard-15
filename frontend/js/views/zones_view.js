window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["zones-view"] = {
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
};
