window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["playlists-view"] = {
  template: `
  <div class="panel">
    <h2>播放清单</h2>
    <p class="lead">有序素材序列；置为可播后才能发布上屏。</p>
    <table>
      <thead><tr><th>编码</th><th>标题</th><th>状态</th><th>过渡</th><th>条目数</th><th>负责人</th></tr></thead>
      <tbody>
        <tr v-for="p in items" :key="p.id">
          <td>{{ p.code }}</td><td>{{ p.title }}</td><td>{{ p.status }}</td>
          <td>{{ p.transition }}</td><td>{{ p.item_count }}</td><td>{{ p.owner }}</td>
        </tr>
      </tbody>
    </table>
  </div>`,
  data() { return { items: [] }; },
  async mounted() { this.items = (await SB.api("/api/playlists")).items; }
};
