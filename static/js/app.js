// ── App state ────────────────────────────────────────────────────────────────
const AppState = {
  activeFilters: {},   // { field: Set(values) }
  searchQuery:   "",
  garments:      [],
};

// ── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initUpload();
  wireHeaderEvents();
  loadFacetsAndRender();
  loadGarments();
});

function wireHeaderEvents() {
  // Search — debounced so we don't hit the API on every keystroke
  const searchInput = document.getElementById("search-input");
  const clearBtn    = document.getElementById("search-clear");
  let debounceTimer;

  searchInput.addEventListener("input", () => {
    AppState.searchQuery = searchInput.value;
    clearBtn.classList.toggle("hidden", !AppState.searchQuery);
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadGarments, 280);
  });

  searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { clearTimeout(debounceTimer); loadGarments(); }
    if (e.key === "Escape") { clearSearchInput(); }
  });

  clearBtn.addEventListener("click", clearSearchInput);

  document.getElementById("upload-btn").addEventListener("click", openUploadModal);
  document.getElementById("clear-filters-btn").addEventListener("click", clearAllFilters);
  document.getElementById("random-btn").addEventListener("click", showRandomGarment);
  document.getElementById("export-btn").addEventListener("click", exportCSV);

  // Close modals on overlay click
  document.getElementById("upload-modal").addEventListener("click", e => {
    if (e.target === e.currentTarget) closeUploadModal();
  });
  document.getElementById("detail-modal").addEventListener("click", e => {
    if (e.target === e.currentTarget) closeDetailModal();
  });

  // Keyboard shortcuts
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      closeDetailModal();
      closeUploadModal();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === "k") {
      e.preventDefault();
      searchInput.focus();
    }
  });
}

function clearSearchInput() {
  AppState.searchQuery = "";
  document.getElementById("search-input").value = "";
  document.getElementById("search-clear").classList.add("hidden");
  loadGarments();
}

// ── Data loading ─────────────────────────────────────────────────────────────
async function loadFacetsAndRender() {
  try {
    const facets = await API.getFacets();
    renderFilters(facets);
  } catch (err) {
    console.error("Facets load failed:", err);
  }
}

async function loadGarments() {
  renderSkeletons(12);
  try {
    const params = buildQueryParams();
    const garments = await API.listGarments(params);
    AppState.garments = garments;
    updateResultCount(garments.length);
    renderGallery(garments);
  } catch (err) {
    showToast("Failed to load images: " + err.message, "error");
    document.getElementById("image-grid").innerHTML =
      `<div class="empty-state"><p style="color:var(--danger)">${err.message}</p></div>`;
  }
}

function buildQueryParams() {
  const params = {};
  if (AppState.searchQuery) params.q = AppState.searchQuery;
  for (const [field, values] of Object.entries(AppState.activeFilters)) {
    if (values.size > 0) params[field] = Array.from(values);
  }
  return params;
}

function updateResultCount(n) {
  document.getElementById("result-count").textContent =
    `${n} image${n !== 1 ? "s" : ""}`;
}

// ── Misc actions ─────────────────────────────────────────────────────────────
async function showRandomGarment() {
  if (!AppState.garments.length) {
    showToast("Upload some images first!");
    return;
  }
  const g = AppState.garments[Math.floor(Math.random() * AppState.garments.length)];
  openDetailModal(g.id);
}

async function exportCSV() {
  try {
    const res = await API.exportCSV();
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = "fashion_library.csv";
    a.click();
    URL.revokeObjectURL(url);
    showToast("CSV downloaded");
  } catch (err) {
    showToast("Export failed: " + err.message, "error");
  }
}

// ── Toast helper ─────────────────────────────────────────────────────────────
function showToast(message, type = "") {
  const el  = document.createElement("div");
  el.className = `toast${type ? " " + type : ""}`;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}
