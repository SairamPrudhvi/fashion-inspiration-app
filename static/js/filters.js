// Builds the filter sidebar from the /api/facets response.
// State is kept in AppState.activeFilters which maps field -> Set of values.

const FILTER_GROUPS = [
  { key: "garment_type",    label: "Garment Type",     facetKey: "garment_types"     },
  { key: "style",           label: "Style",             facetKey: "styles"            },
  { key: "material",        label: "Material",          facetKey: "materials"         },
  { key: "pattern",         label: "Pattern",           facetKey: "patterns"          },
  { key: "season",          label: "Season",            facetKey: "seasons"           },
  { key: "occasion",        label: "Occasion",          facetKey: "occasions"         },
  { key: "consumer_profile",label: "Consumer Profile",  facetKey: "consumer_profiles" },
  { key: "continent",       label: "Continent",         facetKey: "continents"        },
  { key: "country",         label: "Country",           facetKey: "countries"         },
  { key: "city",            label: "City",              facetKey: "cities"            },
  { key: "year",            label: "Year",              facetKey: "years"             },
  { key: "designer",        label: "Designer",          facetKey: "designers"         },
];

function renderFilters(facets) {
  const container = document.getElementById("filters-container");
  const groups = FILTER_GROUPS.filter(g => {
    const vals = facets[g.facetKey];
    return vals && vals.length > 0;
  });

  if (groups.length === 0) {
    container.innerHTML = `<div class="filter-loading">Upload some images to see filter options.</div>`;
    return;
  }

  container.innerHTML = groups.map(g => renderFilterGroup(g, facets[g.facetKey])).join("");

  // Wire up checkbox change events
  container.querySelectorAll("input[type=checkbox]").forEach(cb => {
    cb.addEventListener("change", () => {
      const { field, value } = cb.dataset;
      toggleFilter(field, value, cb.checked);
    });
  });

  // Wire up collapsible headers
  container.querySelectorAll(".filter-group-header").forEach(header => {
    header.addEventListener("click", () => {
      header.closest(".filter-group").classList.toggle("open");
    });
  });
}

function renderFilterGroup(group, values) {
  const hasActive = AppState.activeFilters[group.key] && AppState.activeFilters[group.key].size > 0;
  return `
    <div class="filter-group ${hasActive ? "open" : ""}">
      <div class="filter-group-header">
        <span>${group.label}</span>
        <span class="chevron">›</span>
      </div>
      <div class="filter-group-body">
        ${values.map(v => renderFilterOption(group.key, String(v))).join("")}
      </div>
    </div>`;
}

function renderFilterOption(field, value) {
  const isChecked = AppState.activeFilters[field] && AppState.activeFilters[field].has(value);
  return `
    <label class="filter-option">
      <input type="checkbox" data-field="${field}" data-value="${value}" ${isChecked ? "checked" : ""}>
      <span>${value}</span>
    </label>`;
}

function toggleFilter(field, value, checked) {
  if (!AppState.activeFilters[field]) {
    AppState.activeFilters[field] = new Set();
  }
  if (checked) {
    AppState.activeFilters[field].add(value);
  } else {
    AppState.activeFilters[field].delete(value);
    if (AppState.activeFilters[field].size === 0) {
      delete AppState.activeFilters[field];
    }
  }
  updateActiveFilterTags();
  loadGarments();
}

function clearAllFilters() {
  AppState.activeFilters = {};
  AppState.searchQuery = "";
  document.getElementById("search-input").value = "";
  document.getElementById("search-clear").classList.add("hidden");
  loadFacetsAndRender();
  loadGarments();
}

function updateActiveFilterTags() {
  const container = document.getElementById("active-filter-tags");
  const tags = [];
  for (const [field, values] of Object.entries(AppState.activeFilters)) {
    for (const v of values) {
      const label = FILTER_GROUPS.find(g => g.key === field)?.label || field;
      tags.push({ field, value: v, label });
    }
  }

  container.innerHTML = tags.map(t => `
    <span class="active-tag">
      ${t.label}: ${t.value}
      <button onclick="removeFilterTag('${t.field}','${t.value}')" title="Remove">✕</button>
    </span>`).join("");
}

function removeFilterTag(field, value) {
  if (AppState.activeFilters[field]) {
    AppState.activeFilters[field].delete(value);
    if (AppState.activeFilters[field].size === 0) delete AppState.activeFilters[field];
  }
  // Uncheck the corresponding checkbox
  const cb = document.querySelector(`input[data-field="${field}"][data-value="${value}"]`);
  if (cb) cb.checked = false;
  updateActiveFilterTags();
  loadGarments();
}
