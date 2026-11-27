window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["screens-view"] = {
  template: `
  <div class="panel">
    <h2>屏幕台账</h2>
    <p class="lead">物理终端绑定分区、分辨率与在线状态；正式发布同屏恒一行，双行即账实事故。</p>
    <table>
      <thead><tr><th>编码</th><th>标题</th><th>分区</th><th>分辨率</th><th>状态</th><th>风险</th><th>正式发布</th><th>账实</th></tr></thead>
      <tbody>
        <tr v-for="s in items" :key="s.id">
          <td>{{ s.code }}</td><td>{{ s.title }}</td><td>{{ s.zone_title }}</td>
          <td>{{ s.resolution }}</td>
          <td><span class="badge" :class="s.status==='online'?'':(s.status==='maintenance'?'bad':'warn')">{{ s.status_label }}</span></td>
          <td>{{ s.risk_level }}</td>
          <td>{{ pubCount[s.id] || 0 }} 行<span v-if="pubVersion[s.id]"> · v{{ pubVersion[s.id] }}</span></td>
          <td>
            <span v-if="(pubCount[s.id] || 0) <= 1" class="badge">账实相符</span>
            <span v-else class="badge bad">正式发布不唯一</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() {
    return { items: [], pubCount: {}, pubVersion: {} };
  },
  async mounted() {
    this.items = (await SB.api("/api/screens")).items;
    const pubs = (await SB.api("/api/publish/official")).items;
    const count = {};
    const version = {};
    for (const p of pubs) {
      count[p.screen_id] = (count[p.screen_id] || 0) + 1;
      version[p.screen_id] = p.version;
    }
    this.pubCount = count;
    this.pubVersion = version;
  }
};
