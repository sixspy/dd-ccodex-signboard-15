window.SB = window.SB || {};
SB.token = localStorage.getItem("sb_token") || "";
SB.api = async function(path, opts = {}) {
  const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
  if (SB.token) headers.Authorization = "Bearer " + SB.token;
  const res = await fetch(path, Object.assign({}, opts, { headers }));
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch (e) { data = { raw: text }; }
  if (!res.ok) {
    const msg = (data && (data.detail || data.message)) || res.statusText || "请求失败";
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
};
