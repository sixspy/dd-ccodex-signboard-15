window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["history-view"] = {
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
};
