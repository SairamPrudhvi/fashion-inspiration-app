// Central place for all API calls so the rest of the JS stays clean.

async function apiFetch(path, options = {}) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const body = await res.json(); detail = body.detail || detail; } catch {}
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

const API = {
  listGarments(params = {}) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v === null || v === undefined || v === "") continue;
      if (Array.isArray(v)) v.forEach(item => qs.append(k, item));
      else qs.append(k, v);
    }
    const query = qs.toString();
    return apiFetch(`/api/garments${query ? "?" + query : ""}`);
  },

  getGarment(id) { return apiFetch(`/api/garments/${id}`); },

  uploadGarments(files, designer) {
    const fd = new FormData();
    files.forEach(f => fd.append("files", f));
    if (designer) fd.append("designer", designer);
    return apiFetch("/api/garments/upload", { method: "POST", body: fd });
  },

  deleteGarment(id) {
    return apiFetch(`/api/garments/${id}`, { method: "DELETE" });
  },

  updateAnnotations(id, payload) {
    return apiFetch(`/api/garments/${id}/annotations`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  },

  similarGarments(id) { return apiFetch(`/api/garments/${id}/similar`); },

  getFacets() { return apiFetch("/api/facets"); },

  exportCSV() { return apiFetch("/api/garments/export"); },
};
