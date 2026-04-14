import json
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


class GarmentResponse(BaseModel):
    id: str
    file_path: str
    original_filename: str
    uploaded_at: datetime
    designer: Optional[str] = None

    # AI-generated
    description: Optional[str] = None
    garment_type: Optional[str] = None
    style: Optional[str] = None
    material: Optional[str] = None
    color_palette: List[str] = []
    pattern: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    consumer_profile: Optional[str] = None
    trend_notes: Optional[str] = None
    location_context: Optional[str] = None
    continent: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    confidence: Dict[str, str] = {}

    # Designer annotations
    user_tags: List[str] = []
    user_notes: Optional[str] = None

    @classmethod
    def from_db(cls, db_obj) -> "GarmentResponse":
        data = {col.name: getattr(db_obj, col.name) for col in db_obj.__table__.columns}
        data["color_palette"] = json.loads(data.get("color_palette") or "[]")
        data["user_tags"] = json.loads(data.get("user_tags") or "[]")
        data["confidence"] = json.loads(data.get("confidence") or "{}")
        return cls(**data)


class AnnotationUpdate(BaseModel):
    user_tags: Optional[List[str]] = None
    user_notes: Optional[str] = None


class FacetOptions(BaseModel):
    garment_types: List[str] = []
    styles: List[str] = []
    materials: List[str] = []
    patterns: List[str] = []
    seasons: List[str] = []
    occasions: List[str] = []
    consumer_profiles: List[str] = []
    continents: List[str] = []
    countries: List[str] = []
    cities: List[str] = []
    years: List[int] = []
    designers: List[str] = []
