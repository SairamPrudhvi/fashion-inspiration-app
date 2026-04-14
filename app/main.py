from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import annotations, garments, search

_BASE = Path(__file__).parent.parent
_UPLOAD_DIR = _BASE / "data" / "uploads"
_STATIC_DIR = _BASE / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Fashion Inspiration Library", version="1.0.0", lifespan=lifespan)


# Serve uploaded images at /uploads/<filename>
app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")

# Serve the frontend at /static/…
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# API routers
app.include_router(garments.router)
app.include_router(search.router)
app.include_router(annotations.router)


@app.get("/")
def serve_frontend():
    return FileResponse(str(_STATIC_DIR / "index.html"))


@app.get("/health")
def health():
    return {"status": "ok"}
