from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.garment import Garment
from ..schemas.garment import FacetOptions, GarmentResponse

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/garments", response_model=List[GarmentResponse])
def list_garments(
    q: Optional[str] = Query(None, description="Full-text search across descriptions and annotations"),
    garment_type: Optional[List[str]] = Query(None),
    style: Optional[List[str]] = Query(None),
    material: Optional[List[str]] = Query(None),
    pattern: Optional[List[str]] = Query(None),
    season: Optional[List[str]] = Query(None),
    occasion: Optional[List[str]] = Query(None),
    consumer_profile: Optional[List[str]] = Query(None),
    continent: Optional[List[str]] = Query(None),
    country: Optional[List[str]] = Query(None),
    city: Optional[List[str]] = Query(None),
    year: Optional[List[int]] = Query(None),
    designer: Optional[List[str]] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(60, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Garment)

    # Full-text search — covers AI description, trend notes, location context,
    # and user-authored notes/tags so natural queries like "embroidered neckline"
    # or "artisan market" work across the whole record.
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Garment.description.ilike(like),
                Garment.trend_notes.ilike(like),
                Garment.location_context.ilike(like),
                Garment.user_notes.ilike(like),
                Garment.user_tags.ilike(like),
                Garment.consumer_profile.ilike(like),
                Garment.garment_type.ilike(like),
                Garment.style.ilike(like),
                Garment.material.ilike(like),
                Garment.pattern.ilike(like),
            )
        )

    # Attribute filters — all multi-value (OR within a field, AND across fields)
    if garment_type:
        query = query.filter(Garment.garment_type.in_(garment_type))
    if style:
        query = query.filter(Garment.style.in_(style))
    if material:
        query = query.filter(Garment.material.in_(material))
    if pattern:
        query = query.filter(Garment.pattern.in_(pattern))
    if season:
        query = query.filter(Garment.season.in_(season))
    if occasion:
        query = query.filter(Garment.occasion.in_(occasion))
    if consumer_profile:
        query = query.filter(Garment.consumer_profile.in_(consumer_profile))

    # Location filters
    if continent:
        query = query.filter(Garment.continent.in_(continent))
    if country:
        query = query.filter(Garment.country.in_(country))
    if city:
        query = query.filter(Garment.city.in_(city))
    if year:
        query = query.filter(Garment.year.in_(year))
    if designer:
        query = query.filter(Garment.designer.in_(designer))

    offset = (page - 1) * limit
    rows = query.order_by(Garment.uploaded_at.desc()).offset(offset).limit(limit).all()
    return [GarmentResponse.from_db(g) for g in rows]


@router.get("/facets", response_model=FacetOptions)
def get_facets(db: Session = Depends(get_db)):
    """
    Return all distinct values for every filterable field, derived dynamically
    from the current dataset. The frontend uses this to build the filter panel
    without any hardcoded lists.
    """

    def distinct(col):
        return [
            row[0]
            for row in db.query(col)
            .filter(col.isnot(None))
            .filter(col != "")
            .distinct()
            .all()
        ]

    def distinct_int(col):
        return sorted(
            row[0]
            for row in db.query(col).filter(col.isnot(None)).distinct().all()
        )

    return FacetOptions(
        garment_types=sorted(distinct(Garment.garment_type)),
        styles=sorted(distinct(Garment.style)),
        materials=sorted(distinct(Garment.material)),
        patterns=sorted(distinct(Garment.pattern)),
        seasons=sorted(distinct(Garment.season)),
        occasions=sorted(distinct(Garment.occasion)),
        consumer_profiles=sorted(distinct(Garment.consumer_profile)),
        continents=sorted(distinct(Garment.continent)),
        countries=sorted(distinct(Garment.country)),
        cities=sorted(distinct(Garment.city)),
        years=distinct_int(Garment.year),
        designers=sorted(distinct(Garment.designer)),
    )
