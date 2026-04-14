// Upload modal — handles drag-and-drop, file queue, and batch upload progress.

let _pendingFiles = [];

function openUploadModal() {
  _pendingFiles = [];
  document.getElementById("upload-queue").classList.add("hidden");
  document.getElementById("upload-queue").innerHTML = "";
  document.getElementById("designer-input").value = "";
  document.getElementById("file-input").value = "";
  document.getElementById("start-upload-btn").disabled = true;
  document.getElementById("upload-modal").classList.remove("hidden");
}

function closeUploadModal() {
  document.getElementById("upload-modal").classList.add("hidden");
}

function initUpload() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const uploadBtn = document.getElementById("start-upload-btn");

  dropZone.addEventListener("click", (e) => {
    if (e.target !== fileInput) fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    addFiles(Array.from(fileInput.files));
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-over");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith("image/"));
    addFiles(files);
  });

  uploadBtn.addEventListener("click", startUpload);
}

function addFiles(files) {
  if (!files.length) return;
  _pendingFiles = [..._pendingFiles, ...files];
  renderQueue();
  document.getElementById("start-upload-btn").disabled = false;
}

function renderQueue() {
  const queue = document.getElementById("upload-queue");
  queue.classList.remove("hidden");
  queue.innerHTML = _pendingFiles.map((f, i) => `
    <div class="queue-item" id="queue-item-${i}">
      <span class="queue-item-name">${f.name}</span>
      <span class="queue-status pending" id="queue-status-${i}">Pending</span>
    </div>`).join("");
}

async function startUpload() {
  if (!_pendingFiles.length) return;

  const btn = document.getElementById("start-upload-btn");
  const designer = document.getElementById("designer-input").value.trim();
  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Classifying…`;

  // Upload all at once — the backend handles the loop
  // Show each item as "uploading" while we wait
  _pendingFiles.forEach((_, i) => setQueueStatus(i, "uploading", "Classifying…"));

  try {
    const results = await API.uploadGarments(_pendingFiles, designer);
    results.forEach((_, i) => setQueueStatus(i, "done", "Done ✓"));
    btn.textContent = `Done — ${results.length} image${results.length !== 1 ? "s" : ""} added`;
    setTimeout(() => {
      closeUploadModal();
      loadFacetsAndRender();
      loadGarments();
    }, 900);
  } catch (err) {
    _pendingFiles.forEach((_, i) => setQueueStatus(i, "error", "Error"));
    btn.textContent = "Upload failed";
    btn.disabled = false;
    showToast(err.message, "error");
  }
}

function setQueueStatus(index, cls, text) {
  const el = document.getElementById(`queue-status-${index}`);
  if (el) {
    el.className = `queue-status ${cls}`;
    el.textContent = text;
  }
}
