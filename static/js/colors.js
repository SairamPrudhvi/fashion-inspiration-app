// Maps common fashion color names to approximate CSS colors for swatch display.
// CSS supports many named colors natively (navy, ivory, teal…) so we only
// need entries for names that differ from their CSS counterpart.

const COLOR_MAP = {
  // Whites / Neutrals
  "ivory":         "#FFFFF0",
  "cream":         "#FFFDD0",
  "off-white":     "#FAF9F6",
  "off white":     "#FAF9F6",
  "ecru":          "#C2B280",
  "linen":         "#FAF0E6",
  "bone":          "#E8DCC8",
  "sand":          "#C2B280",
  "stone":         "#928E85",
  "pebble":        "#9D9083",

  // Beiges / Browns
  "camel":         "#C19A6B",
  "warm beige":    "#D4B896",
  "taupe":         "#483C32",
  "tan":           "#D2B48C",
  "khaki":         "#C3B091",
  "mocha":         "#967969",
  "chocolate":     "#7B3F00",
  "cognac":        "#9A463D",
  "rust":          "#B7410E",
  "terracotta":    "#E2725B",
  "sienna":        "#A0522D",
  "auburn":        "#A52A2A",

  // Reds / Pinks
  "burgundy":      "#800020",
  "wine":          "#722F37",
  "bordeaux":      "#5C1A1A",
  "cherry":        "#DE3163",
  "rose":          "#FF007F",
  "blush":         "#FFB6C1",
  "dusty rose":    "#DCAE96",
  "dusty pink":    "#D4A0A0",
  "hot pink":      "#FF69B4",
  "fuchsia":       "#FF00FF",
  "coral":         "#FF7F50",
  "salmon":        "#FA8072",

  // Oranges / Yellows
  "mustard":       "#FFDB58",
  "golden":        "#FFD700",
  "amber":         "#FFBF00",
  "saffron":       "#F4C430",
  "turmeric":      "#CDA323",
  "ochre":         "#CC7722",
  "burnt orange":  "#CC5500",

  // Greens
  "olive":         "#808000",
  "sage":          "#BCB88A",
  "forest green":  "#228B22",
  "bottle green":  "#006A4E",
  "emerald":       "#50C878",
  "mint":          "#98FF98",
  "jade":          "#00A86B",
  "hunter green":  "#355E3B",
  "army green":    "#4B5320",
  "pistachio":     "#93C572",
  "eucalyptus":    "#44D7A8",

  // Blues
  "navy":          "#001F5B",
  "navy blue":     "#000080",
  "cobalt":        "#0047AB",
  "royal blue":    "#4169E1",
  "steel blue":    "#4682B4",
  "sky blue":      "#87CEEB",
  "powder blue":   "#B0E0E6",
  "denim":         "#1560BD",
  "indigo":        "#4B0082",
  "electric blue": "#7DF9FF",
  "baby blue":     "#89CFF0",
  "ice blue":      "#D6ECFA",

  // Purples
  "lavender":      "#E6E6FA",
  "lilac":         "#C8A2C8",
  "mauve":         "#E0B0FF",
  "violet":        "#EE82EE",
  "plum":          "#8E4585",
  "grape":         "#6F2DA8",
  "aubergine":     "#3D0C02",
  "eggplant":      "#614051",

  // Grays / Blacks
  "charcoal":      "#36454F",
  "graphite":      "#474A51",
  "slate":         "#708090",
  "light gray":    "#D3D3D3",
  "light grey":    "#D3D3D3",
  "dark gray":     "#404040",
  "dark grey":     "#404040",
  "off-black":     "#1C1C1C",

  // Metallics
  "gold":          "#FFD700",
  "silver":        "#C0C0C0",
  "bronze":        "#CD7F32",
  "copper":        "#B87333",
  "champagne":     "#F7E7CE",
};

function getColorCSS(name) {
  if (!name) return "#ccc";
  const lower = name.toLowerCase().trim();
  return COLOR_MAP[lower] || lower;  // CSS handles many color names natively
}

function renderSwatches(colors) {
  if (!colors || colors.length === 0) return "";
  return `<div class="color-swatches">
    ${colors.map(c => `<span class="color-swatch" style="background:${getColorCSS(c)}" title="${c}" data-name="${c}"></span>`).join("")}
    <span class="color-swatch-label">${colors.join(", ")}</span>
  </div>`;
}
