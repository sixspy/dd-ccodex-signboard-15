window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["dashboard-view"] = {
  template: `
  <div class="panel">
    <h2>总览</h2>
    <p class="lead">{{ meta.skeleton || "加载中…" }}</p>
    <div class="stats">
      <div class="stat" v-for="s in cards" :key="s.k"><b :style="s.danger ? 'color:var(--danger)' : ''">{{ s.v }}</b><span>{{ s.l }}</span></div>
    </div>
    <p class="err" v-if="dualOfficialScreens.length">
      账实红灯：同屏正式发布不唯一 → {{ dualOfficialScreens.join("、") }}
    </p>
    <p class="hint" v-else>同屏正式发布均唯一，发布互斥闸口闭合中。</p>
  </div>`,
  data() { return { meta: {}, cards: [], dualOfficialScreens: [] }; },
  async mounted() {
    const d = await SB.api("/api/dashboard");
    this.meta = d;
    const pubs = (await SB.api("/api/publish/official")).items;
    const perScreen = {};
    for (const p of pubs) {
      perScreen[p.screen_code] = (perScreen[p.screen_code] || 0) + 1;
    }
    this.dualOfficialScreens = Object.keys(perScreen).filter(code => perScreen[code] > 1);
    const history = await SB.api("/api/history?limit=300");
    const contentions = history.items.filter(h => h.entity_kind.endsWith("_contention")).length;
    this.cards = [
      { k: "screens", l: "屏幕总数", v: d.screens },
      { k: "online", l: "在线屏幕", v: d.online_screens },
      { k: "assets", l: "可播素材", v: d.ready_assets },
      { k: "pubs", l: "正式发布", v: d.official_publications },
      { k: "shadows", l: "待升正影子", v: d.open_shadows },
      { k: "ov", l: "生效覆盖", v: d.active_overrides },
      { k: "contention", l: "争用留痕（败方零正式）", v: contentions, danger: contentions > 0 },
      { k: "dual", l: "双正式账实事故屏", v: this.dualOfficialScreens.length, danger: this.dualOfficialScreens.length > 0 },
    ];
  }
};
