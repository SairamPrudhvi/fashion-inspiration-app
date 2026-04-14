# Fashion Inspiration Library

I built this to tackle the core problem in the brief: design teams end up with thousands of inspiration photos scattered across phones and shared folders, and there's no good way to actually find anything once the collection grows past a few hundred images.

The app uploads garment photos, runs each one through a vision AI model to extract attributes, and stores everything in a searchable database. The filter panel is built dynamically from whatever's actually in your library — so you never have to choose from a hardcoded dropdown of styles that don't match what you've uploaded.

---

## Getting started

You'll need Python 3.11+. There's no Node, no Docker, no build step.

```bash
git clone <repo>
cd fashion-inspiration-app

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Open .env and add your Groq API key
# Get a free key at https://console.groq.com/keys (no credit card needed)

uvicorn app.main:app --reload
```

Open http://localhost:8000.

**No API key?** The app still runs — every upload gets a static placeholder classification so you can poke around the UI. You'll notice every image comes back as a camel blazer, which is the giveaway.

---

## What it does

- **Upload** single or multiple garment images at once. Drag-and-drop works.
- **AI classification** runs on each image via Groq (Llama 4 Scout) and returns a natural-language description plus structured attributes: garment type, style, material, colour palette, pattern, season, occasion, consumer profile, trend notes, and location context.
- **Colour swatches** render as actual coloured circles using a hand-mapped dictionary of ~80 common fashion colour names.
- **Filter panel** is built from whatever's in your library — if nobody's uploaded anything from Asia yet, Asia won't appear in the continent filter.
- **Full-text search** covers the AI description, trend notes, location context, and your own notes and tags. So you can search for "embroidered neckline" or "artisan market" and find images whose description mentions those things.
- **Annotations** let you add your own tags and notes to any image. These are stored separately from AI-generated fields so the original classification is always preserved.
- **Similar images** — the detail view shows other garments with the same type and style. Simple attribute matching, not embedding similarity, but effective enough for a POC.
- **Export CSV** downloads your full library with all AI and annotation fields.
- **Surprise me** opens a random image from your library — handy when you want a quick jolt of inspiration without knowing what you're looking for.
- **Confidence flagging** — the model returns a confidence level for each attribute. Low-confidence classifications show a warning badge on the card.

---

## Architecture

```
app/
  main.py          FastAPI app, mounts static files and API routers
  config.py        Settings loaded from .env via python-dotenv
  database.py      SQLAlchemy engine and session factory (SQLite)
  models/
    garment.py     SQLAlchemy ORM model — one table with all attributes
  schemas/
    garment.py     Pydantic schemas for request/response serialisation
  services/
    classifier.py  Groq API integration + JSON parsing + mock fallback
    storage.py     File upload handling (UUID-named files on disk)
    export.py      CSV serialisation
  routers/
    garments.py    Upload, get, delete, export, similar
    search.py      List with filters + full-text search, facets endpoint
    annotations.py PATCH endpoint for user tags and notes

static/            Vanilla JS + CSS frontend, served by FastAPI
  css/
    main.css       Layout, cards, modals
    components.css Colour swatches, pills, confidence badges, toasts
  js/
    api.js         All fetch() wrappers in one place
    colors.js      CSS colour mapping for 80+ fashion colour names
    gallery.js     Image grid rendering and skeleton loading
    filters.js     Dynamic filter sidebar from /api/facets
    detail.js      Detail modal with colour swatches and similar images
    upload.js      Drag-and-drop upload with per-file status
    app.js         App state, event wiring, search debounce

eval/
  run_eval.py      CLI evaluation script
  metrics.py       Per-field accuracy, macro average, report formatting
  labels_template.jsonl  Ground truth template (10 example entries)

tests/
  conftest.py      In-memory SQLite DB, TestClient, mock classifier
  unit/            Parser unit tests
  integration/     Filter, search, annotation tests against real endpoints
  e2e/             Full workflow tests through the API
```

**Database**: A single SQLite file (`data/fashion.db`) with one `garments` table. JSON arrays (colour palette, user tags, confidence scores) are stored as JSON strings — SQLite doesn't have a native array type, but this works fine for a POC.

**Frontend**: Plain HTML + vanilla JS, no build step. Scripts are loaded in dependency order so ES module syntax isn't needed. State lives in a single `AppState` object in `app.js`. Filter state uses `Set` objects for O(1) membership checks.

**Classifier**: The prompt requests a strict JSON schema and strips markdown fences if the model adds them anyway. If the first response can't be parsed, there's one retry with a correction prompt before raising an error.

---

## Running the tests

```bash
pytest tests/ -v
```

The test suite uses an in-memory SQLite database and patches `classify_image` so no real API calls are made during tests. Each test rolls back after it finishes so there's no state leakage between them.

**Unit tests** (`tests/unit/test_classifier.py`): Exercise `parse_model_output` against valid JSON, markdown-wrapped responses, missing optional fields, and broken JSON. No mocking needed since the parser is pure Python.

**Integration tests** (`tests/integration/`): Drive the API endpoints through FastAPI's TestClient. Cover single and batch upload, every filter type including location and time, full-text search across AI and user fields, and annotation CRUD.

**End-to-end tests** (`tests/e2e/test_e2e.py`): Simulate a complete designer workflow — upload a batch of images with different locations, filter to find specific ones, annotate, and verify the annotation is searchable. Also covers delete and similar-images.

---

## Model evaluation

The evaluation script classifies images from a labelled ground truth file and reports per-attribute accuracy.

```bash
# Add images to eval/sample_images/ and fill in eval/labels_template.jsonl
# then:

python eval/run_eval.py \
  --images-dir eval/sample_images/ \
  --labels-file eval/labels_template.jsonl \
  --output-json eval/results.json
```

The labels file (`eval/labels_template.jsonl`) has 10 example entries showing the expected format. For the full 50-100 image evaluation, download images from [Pexels](https://www.pexels.com/search/fashion/) or another open dataset and manually label them.

**What the model is good at**: Visual attributes like garment type, pattern, and season are generally high confidence. Colour palette extraction is solid — the model reliably identifies the 3-5 dominant colours by descriptive name. Style classification works well for clear archetypes (streetwear, formal, bohemian) and gets fuzzier at the edges between them.

**Where it struggles**: Location context is essentially a guess unless there are strong cultural visual cues in the image — a recognisable backdrop, traditional textile, or signage in frame. `consumer_profile` and `trend_notes` are inherently subjective; even human annotators would disagree. Material prediction is reasonable for visually distinct fabrics (denim, leather, velvet) and less reliable for synthetics that look like natural fibres.

**What I'd improve with more time**: The most impactful change would be few-shot prompting — showing the model 3-5 examples of well-labelled garments before the target image. This typically lifts accuracy noticeably on subjective fields. For location specifically, I'd add a follow-up question only when the first response returns null, with a more targeted prompt around visible cultural signals. Longer term, a retrieval-augmented approach that shows visually similar already-labelled images as context would be more reliable than pure zero-shot inference.

---

## Simplifying assumptions

A few things that are intentionally out of scope for this POC:

- **Full-text search uses SQL LIKE, not FTS5**. SQLite has a proper full-text search extension that would be faster and support tokenisation. For a library with tens of thousands of images I'd migrate to that — for a few hundred, LIKE is fine.
- **No pagination UI**. The API supports `page` and `limit` parameters, but the frontend just loads the first 60 results. A real version would need infinite scroll or pagination controls.
- **Location data comes from the AI alone**. There's no EXIF extraction, so if a photo was taken in Tokyo but the garment has no visual cues, the model will return null. In production I'd read EXIF GPS coordinates and reverse-geocode them.
- **No image resizing before upload**. Large images work fine but a production app would resize to a reasonable width before encoding to keep latency down.
- **No authentication**. Anyone who can reach the server can upload and delete images. Fine for a local tool, not for a shared deployment.
- **Similar images is attribute-based, not semantic**. A proper similarity search would embed each image or its description and use nearest-neighbour search. The current approach matches on garment type and style, which is a reasonable heuristic but misses nuanced visual similarity.
- **No browser E2E tests**. The e2e suite drives the backend API through TestClient, which covers the full contract, but doesn't verify the frontend JavaScript. Playwright tests for the upload flow and filter interaction would close that gap.
