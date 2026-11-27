window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["windows-view"] = {
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
};
