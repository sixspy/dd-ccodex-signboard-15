window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["history-view"] = {
  template: `
  <div class="panel">
    <h2>变更历史</h2>
    <p class="lead">发布、撤屏、覆盖与台账变更同源可追溯；争用败方正式区零改，只在此与审计留痕。</p>
    <div class="row-form">
      <button class="ghost" @click="onlyContention = !onlyContention">
        {{ onlyContention ? "显示全部" : "只看争用痕" }}
      </button>
      <span class="hint">争用痕 {{ contentions.length }} 条 / 共 {{ items.length }} 条</span>
    </div>
    <table>
      <thead><tr><th>ID</th><th>实体</th><th>动作</th><th>详情</th><th>操作者</th></tr></thead>
      <tbody>
        <tr v-for="h in shown" :key="h.id" :style="h.entity_kind.endsWith('_contention') ? 'background:rgba(255,107,107,.08)' : ''">
          <td>{{ h.id }}</td><td>{{ h.entity_kind }}#{{ h.entity_id }}</td>
          <td><span :class="h.entity_kind.endsWith('_contention') ? 'badge bad' : ''">{{ h.action }}</span></td>
          <td>{{ h.detail }}</td><td>{{ h.actor }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [], onlyContention: false }; },
  computed: {
    contentions() { return this.items.filter(h => h.entity_kind.endsWith("_contention")); },
    shown() { return this.onlyContention ? this.contentions : this.items; }
  },
  async mounted() { this.items = (await SB.api("/api/history?limit=300")).items; }
};
