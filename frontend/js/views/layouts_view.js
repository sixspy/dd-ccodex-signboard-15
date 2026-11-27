window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["layouts-view"] = {
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
};
