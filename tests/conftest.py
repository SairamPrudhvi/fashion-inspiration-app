"""
Shared pytest fixtures.

Key design decisions:
- Uses an in-memory SQLite database so tests are fully isolated and never
  touch the real data/fashion.db file.
- Patches classifier.classify_image globally so no real Claude API calls
  are made.  Each test can override the mock return value if needed.
- Uses FastAPI's TestClient (synchronous) — no asyncio overhead.
"""

import io
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Minimal mock classification result (mirrors the real schema) ─────────────
MOCK_CLASSIFICATION = {
    "description": "A classic single-button wool blazer in a warm camel tone with a notched lapel.",
    "garment_type": "blazer",
    "style": "business casual",
    "material": "wool blend",
    "color_palette": ["camel", "ivory"],
    "pattern": "solid",
    "season": "fall/winter",
    "occasion": "business casual",
    "consumer_profile": "young urban professional",
    "trend_notes": "quiet luxury",
    "location_context": "Western European boutique",
    "continent": "Europe",
    "country": "France",
    "city": "Paris",
    "year": 2023,
    "month": None,
    "confidence": {
        "garment_type": "high",
        "style": "high",
        "material": "medium",
        "color_palette": "high",
        "pattern": "high",
        "season": "high",
        "occasion": "high",
        "consumer_profile": "medium",
        "trend_notes": "medium",
        "continent": "medium",
        "country": "low",
        "city": "low",
    },
}


# ── DB fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_engine():
    """Single in-memory SQLite engine for the whole test session."""
    from app.database import Base
    from app.models import garment  # noqa: F401 — registers model with Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(test_engine):
    """
    Function-scoped DB session that rolls back after each test.
    This gives us full isolation without recreating tables.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ── FastAPI client ────────────────────────────────────────────────────────────

@pytest.fixture
def client(db, tmp_path, monkeypatch):
    """
    TestClient wired to the in-memory DB and a temp upload directory.
    Also patches classify_image so no API calls escape during tests.
    """
    from app.main import app
    from app.database import get_db
    import app.services.storage as storage_module
    import app.config as config_module

    # Override DB dependency
    app.dependency_overrides[get_db] = lambda: db

    # Redirect file writes to a temp directory
    monkeypatch.setattr(storage_module, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(config_module, "UPLOAD_DIR", tmp_path)

    with patch("app.services.classifier.classify_image", return_value=MOCK_CLASSIFICATION.copy()):
        with TestClient(app) as c:
            yield c

    app.dependency_overrides.clear()


# ── Sample data helpers ───────────────────────────────────────────────────────

def make_garment(db, **overrides):
    """Insert a Garment row directly into the test DB."""
    from app.models.garment import Garment

    defaults = dict(
        id=str(uuid.uuid4()),
        file_path="placeholder.jpg",
        original_filename="placeholder.jpg",
        uploaded_at=datetime.now(timezone.utc),
        designer="test_designer",
        description="A test garment description.",
        garment_type="dress",
        style="casual",
        material="cotton",
        color_palette=json.dumps(["white", "floral red"]),
        pattern="floral",
        season="spring/summer",
        occasion="casual everyday",
        consumer_profile="young urban professional",
        trend_notes="cottagecore",
        location_context="French market",
        continent="Europe",
        country="France",
        city="Lyon",
        year=2023,
        month=None,
        confidence=json.dumps({"garment_type": "high"}),
        user_tags=json.dumps([]),
        user_notes="",
    )
    defaults.update(overrides)
    g = Garment(**defaults)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@pytest.fixture
def sample_garments(db):
    """A small set of varied garments for filter/search tests."""
    return [
        make_garment(db, garment_type="dress",  style="casual",    material="cotton",
                     continent="Europe",       country="France",   city="Paris",  year=2023),
        make_garment(db, garment_type="jacket", style="streetwear", material="denim",
                     continent="North America",country="USA",      city="New York", year=2024),
        make_garment(db, garment_type="blazer", style="formal",    material="wool blend",
                     continent="Europe",       country="Italy",    city="Milan", year=2022),
        make_garment(db, garment_type="skirt",  style="bohemian",  material="linen",
                     continent="Asia",         country="Japan",    city="Tokyo", year=2023,
                     user_tags=json.dumps(["handmade", "sustainable"]),
                     user_notes="Seen at Shimokitazawa vintage market"),
    ]


@pytest.fixture
def minimal_image_bytes():
    """A valid 10×10 JPEG as raw bytes — used to simulate file uploads."""
    try:
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), color=(200, 150, 100)).save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        # Minimal valid JPEG header fallback (1×1 white pixel)
        return (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
            b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e\xc0"
            b"\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01"
            b"\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03"
            b"\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\x0a"
            b"\xff\xd9"
        )
