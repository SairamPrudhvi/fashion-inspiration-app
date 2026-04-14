// Renders the image grid and individual cards.

function renderGallery(garments) {
  const grid = document.getElementById("image-grid");

  if (!garments || garments.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">◈</div>
        <h2>No results found</h2>
        <p>Try adjusting your filters or search terms, or upload some new images.</p>
        <button class="btn-primary" onclick="openUploadModal()">Upload images</button>
      </div>`;
    return;
  }

  grid.innerHTML = `<div class="grid-container" id="grid-inner"></div>`;
  const inner = document.getElementById("grid-inner");
  inner.innerHTML = garments.map(renderCard).join("");
}

function renderCard(g) {
  const location = [g.city, g.country, g.continent].filter(Boolean).join(", ");
  const hasAnnotations = (g.user_tags && g.user_tags.length > 0) || (g.user_notes && g.user_notes.trim());
  const overallConf = inferOverallConfidence(g.confidence);

  const swatchHtml = g.color_palette && g.color_palette.length
    ? `<div class="attr-pills">${g.color_palette.slice(0, 4).map(c =>
        `<span class="color-swatch" style="background:${getColorCSS(c)};width:12px;height:12px;border-radius:50%;display:inline-block;border:1px solid rgba(0,0,0,.1);flex-shrink:0" title="${c}"></span>`
      ).join("")}</div>`
    : "";

  return `
    <div class="image-card" onclick="openDetailModal('${g.id}')">
      <div class="card-thumb">
        <img src="/uploads/${g.file_path}" alt="${g.original_filename}" loading="lazy">
        ${overallConf === "low" ? `<span class="confidence-badge confidence-low" title="Low confidence classification">?</span>` : ""}
      </div>
      <div class="card-body">
        <div class="card-title">${g.garment_type || "Unknown"} · ${g.style || ""}</div>
        <div class="card-subtitle">${g.material || ""}${g.pattern && g.pattern !== "solid" ? " · " + g.pattern : ""}</div>
        ${location ? `<div class="card-location">📍 ${location}</div>` : ""}
        ${swatchHtml}
        ${hasAnnotations ? `<div class="card-annotated" style="margin-top:4px">✎ annotated</div>` : ""}
      </div>
    </div>`;
}

function inferOverallConfidence(confidence) {
  if (!confidence || Object.keys(confidence).length === 0) return "medium";
  const vals = Object.values(confidence);
  const lowCount = vals.filter(v => v === "low").length;
  if (lowCount >= vals.length * 0.5) return "low";
  if (lowCount > 0) return "medium";
  return "high";
}

function renderSkeletons(count = 12) {
  const grid = document.getElementById("image-grid");
  grid.innerHTML = `<div class="grid-container">${Array(count).fill(0).map(() => `
    <div class="skeleton-card">
      <div class="skeleton skeleton-thumb"></div>
      <div class="skeleton skeleton-line"></div>
      <div class="skeleton skeleton-line-short"></div>
    </div>`).join("")}</div>`;
}
