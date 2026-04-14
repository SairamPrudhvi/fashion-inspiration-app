import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime
from ..database import Base


class Garment(Base):
    __tablename__ = "garments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    designer = Column(String)

    # ── AI-generated fields ────────────────────────────────────────────────
    description = Column(Text)
    garment_type = Column(String)
    style = Column(String)
    material = Column(String)
    color_palette = Column(Text, default="[]")   # JSON array of color-name strings
    pattern = Column(String)
    season = Column(String)
    occasion = Column(String)
    consumer_profile = Column(String)
    trend_notes = Column(Text)
    location_context = Column(Text)
    continent = Column(String)
    country = Column(String)
    city = Column(String)
    year = Column(Integer)
    month = Column(Integer)
    # Per-field confidence from the model: {"garment_type": "high", ...}
    confidence = Column(Text, default="{}")

    # ── Designer annotations (clearly separated from AI output) ───────────
    user_tags = Column(Text, default="[]")   # JSON array of tag strings
    user_notes = Column(Text, default="")

    # ── Helpers ───────────────────────────────────────────────────────────
    def get_color_palette(self) -> list:
        return json.loads(self.color_palette or "[]")

    def get_user_tags(self) -> list:
        return json.loads(self.user_tags or "[]")

    def get_confidence(self) -> dict:
        return json.loads(self.confidence or "{}")
