window.SB_VIEWS = window.SB_VIEWS || {};
window.SB_VIEWS["assets-view"] = {
  template: `
  <div>
    <div class="panel">
      <h2>素材台账</h2>
      <p class="lead">图片 / 视频 / 网页页 / 滚动条，可播后才能进清单。</p>
      <div class="row-form">
        <input v-model="form.code" placeholder="编码" />
        <input v-model="form.title" placeholder="标题" />
        <select v-model="form.kind"><option>image</option><option>video</option><option>html</option><option>ticker</option></select>
        <input v-model="form.resolution" placeholder="分辨率" />
        <select v-model="form.status"><option>draft</option><option>ready</option></select>
        <button class="primary" @click="create">登记素材</button>
      </div>
      <p class="err" v-if="error">{{ error }}</p>
    </div>
    <div class="panel">
      <table>
        <thead><tr><th>编码</th><th>标题</th><th>种类</th><th>时长</th><th>分辨率</th><th>状态</th></tr></thead>
        <tbody>
          <tr v-for="a in items" :key="a.id">
            <td>{{ a.code }}</td><td>{{ a.title }}</td><td>{{ a.kind_label }}</td>
            <td>{{ a.duration_sec }}s</td><td>{{ a.resolution }}</td><td>{{ a.status_label }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>`,
  data() { return { items: [], error: "", form: { code: "", title: "", kind: "image", resolution: "1920x1080", status: "draft", duration_sec: 12 } }; },
  async mounted() { await this.reload(); },
  methods: {
    async reload() { this.items = (await SB.api("/api/assets")).items; },
    async create() {
      this.error = "";
      try { await SB.api("/api/assets", { method: "POST", body: JSON.stringify(this.form) }); await this.reload(); }
      catch (e) { this.error = e.message; }
    }
  }
};
