// Image detail modal — shows AI classification, color swatches,
// confidence indicators, similar images, and the annotation form.

async function openDetailModal(id) {
  const overlay = document.getElementById("detail-modal");
  const content = document.getElementById("detail-content");
  overlay.classList.remove("hidden");
  content.innerHTML = `<div style="padding:40px;text-align:center;color:#717171">Loading…</div>`;

  try {
    const garment = await API.getGarment(id);
    content.innerHTML = renderDetail(garment);
    initAnnotationForm(garment);
    loadSimilar(id);
  } catch (err) {
    content.innerHTML = `<div style="padding:40px;color:#D94F3D">Failed to load: ${err.message}</div>`;
  }
}

function closeDetailModal() {
  document.getElementById("detail-modal").classList.add("hidden");
  // Reload gallery in case annotations changed
  loadGarments();
}

function renderDetail(g) {
  const location = [g.city, g.country, g.continent].filter(Boolean).join(", ");
  const conf = g.confidence || {};

  const attrRows = [
    { key: "Garment type", val: g.garment_type, field: "garment_type" },
    { key: "Style",        val: g.style,         field: "style"        },
    { key: "Material",     val: g.material,       field: "material"     },
    { key: "Pattern",      val: g.pattern,        field: "pattern"      },
    { key: "Season",       val: g.season,         field: "season"       },
    { key: "Occasion",     val: g.occasion,       field: "occasion"     },
    { key: "Consumer",     val: g.consumer_profile,field: "consumer_profile"},
    { key: "Trend notes",  val: g.trend_notes,    field: "trend_notes"  },
    { key: "Location",     val: location,         field: "continent"    },
    { key: "Designer",     val: g.designer,       field: null           },
    { key: "Uploaded",     val: formatDate(g.uploaded_at), field: null  },
  ].filter(r => r.val);

  const confBadge = (field) => {
    const c = conf[field];
    if (!c || c === "high") return "";
    return `<span class="low-confidence" title="${c} confidence">${c === "low" ? "⚠ low conf" : "~ medium conf"}</span>`;
  };

  return `
    <div class="detail-image-col">
      <img src="/uploads/${g.file_path}" alt="${g.original_filename}">
    </div>
    <div class="detail-info-col">

      <!-- Header -->
      <div style="margin-bottom:16px">
        <h2 style="font-size:18px;font-weight:700;text-transform:capitalize;margin-bottom:4px">
          ${g.garment_type || "Garment"} · ${g.style || ""}
        </h2>
        <div style="font-size:12px;color:#717171">${g.original_filename}</div>
      </div>

      <!-- Description -->
      <div class="detail-section">
        <div class="detail-section-label">Description <span class="ai-badge">AI</span></div>
        <p class="detail-description">${g.description || "No description available."}</p>
      </div>

      <!-- Color palette -->
      ${g.color_palette && g.color_palette.length ? `
        <div class="detail-section">
          <div class="detail-section-label">Color Palette <span class="ai-badge">AI</span></div>
          ${renderSwatches(g.color_palette)}
        </div>` : ""}

      <!-- Attributes -->
      <div class="detail-section">
        <div class="detail-section-label">Attributes <span class="ai-badge">AI</span></div>
        <div class="detail-attrs">
          ${attrRows.map(r => `
            <div class="attr-row">
              <span class="attr-key">${r.key}</span>
              <span class="attr-val">
                ${r.val}
                ${r.field ? confBadge(r.field) : ""}
              </span>
            </div>`).join("")}
        </div>
      </div>

      <!-- Designer annotations -->
      <div class="detail-section">
        <div class="detail-section-label">Your Annotations <span class="user-badge">Designer</span></div>
        <div id="annotation-form-${g.id}">
          ${renderAnnotationForm(g)}
        </div>
      </div>

      <!-- Similar images -->
      <div class="detail-section" id="similar-section-${g.id}">
        <div class="detail-section-label">Similar Items</div>
        <div id="similar-grid-${g.id}" class="similar-grid">
          <div style="color:#717171;font-size:12px">Loading…</div>
        </div>
      </div>

      <!-- Actions -->
      <div class="detail-actions">
        <button class="btn-danger" onclick="confirmDelete('${g.id}')">Delete image</button>
      </div>
    </div>`;
}

function renderAnnotationForm(g) {
  const tags = (g.user_tags || []).map(t =>
    `<span class="tag-pill">${t}<button onclick="removeTagPill(this,'${g.id}')" data-tag="${t}">✕</button></span>`
  ).join("");

  return `
    <div class="tag-input-wrap" id="tag-wrap-${g.id}" onclick="document.getElementById('tag-text-${g.id}').focus()">
      <span id="tag-pills-${g.id}">${tags}</span>
      <input id="tag-text-${g.id}" class="tag-input" placeholder="${g.user_tags && g.user_tags.length ? "" : "Add tags…"}"
        data-garment="${g.id}" onkeydown="handleTagInput(event, '${g.id}')">
    </div>
    <textarea id="notes-${g.id}" class="notes-textarea" placeholder="Your observations, inspirations, design notes…">${g.user_notes || ""}</textarea>
    <div style="display:flex;align-items:center;gap:8px;margin-top:8px">
      <button class="btn-primary" onclick="saveAnnotations('${g.id}')" style="padding:6px 12px;font-size:12px">Save</button>
      <span class="save-status" id="save-status-${g.id}"></span>
    </div>`;
}

function initAnnotationForm(g) {
  // Nothing extra needed — event handlers are inline
}

function handleTagInput(event, garmentId) {
  if (event.key === "Enter" || event.key === ",") {
    event.preventDefault();
    const input = document.getElementById(`tag-text-${garmentId}`);
    const val = input.value.replace(",", "").trim();
    if (val) {
      addTagPill(garmentId, val);
      input.value = "";
    }
  }
  if (event.key === "Backspace" && event.target.value === "") {
    const pillsEl = document.getElementById(`tag-pills-${garmentId}`);
    const pills = pillsEl.querySelectorAll(".tag-pill");
    if (pills.length > 0) pills[pills.length - 1].remove();
  }
}

function addTagPill(garmentId, tag) {
  const pillsEl = document.getElementById(`tag-pills-${garmentId}`);
  const span = document.createElement("span");
  span.className = "tag-pill";
  span.innerHTML = `${tag}<button onclick="removeTagPill(this,'${garmentId}')" data-tag="${tag}">✕</button>`;
  pillsEl.appendChild(span);
}

function removeTagPill(btn, garmentId) {
  btn.closest(".tag-pill").remove();
}

function getCurrentTags(garmentId) {
  const pillsEl = document.getElementById(`tag-pills-${garmentId}`);
  return Array.from(pillsEl.querySelectorAll(".tag-pill")).map(p => {
    // Text content minus the × button text
    return p.childNodes[0].textContent.trim();
  });
}

async function saveAnnotations(garmentId) {
  const tags = getCurrentTags(garmentId);
  const notes = document.getElementById(`notes-${garmentId}`)?.value || "";
  const statusEl = document.getElementById(`save-status-${garmentId}`);

  try {
    await API.updateAnnotations(garmentId, { user_tags: tags, user_notes: notes });
    statusEl.textContent = "Saved ✓";
    setTimeout(() => { statusEl.textContent = ""; }, 2000);
  } catch (err) {
    statusEl.textContent = "Error: " + err.message;
    statusEl.style.color = "var(--danger)";
  }
}

async function loadSimilar(garmentId) {
  const container = document.getElementById(`similar-grid-${garmentId}`);
  const section = document.getElementById(`similar-section-${garmentId}`);
  if (!container) return;

  try {
    const similar = await API.similarGarments(garmentId);
    if (!similar || similar.length === 0) {
      section.style.display = "none";
      return;
    }
    container.innerHTML = similar.map(g => `
      <div class="similar-thumb" onclick="openDetailModal('${g.id}')">
        <img src="/uploads/${g.file_path}" alt="${g.original_filename}" loading="lazy">
      </div>`).join("");
  } catch {
    section.style.display = "none";
  }
}

async function confirmDelete(garmentId) {
  if (!confirm("Delete this image? This cannot be undone.")) return;
  try {
    await API.deleteGarment(garmentId);
    closeDetailModal();
    showToast("Image deleted");
    loadFacetsAndRender();
    loadGarments();
  } catch (err) {
    showToast("Delete failed: " + err.message, "error");
  }
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}
