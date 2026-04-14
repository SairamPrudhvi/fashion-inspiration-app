import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.garment import Garment
from ..schemas.garment import AnnotationUpdate, GarmentResponse

router = APIRouter(prefix="/api/garments", tags=["annotations"])


@router.patch("/{garment_id}/annotations", response_model=GarmentResponse)
def update_annotations(
    garment_id: str,
    payload: AnnotationUpdate,
    db: Session = Depends(get_db),
):
    """
    Update designer annotations on a garment. Only the fields present in the
    request body are changed — pass null to clear a field.

    These annotations are stored separately from AI-generated attributes so
    the original classification is always preserved.
    """
    garment = db.query(Garment).filter(Garment.id == garment_id).first()
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")

    if payload.user_tags is not None:
        cleaned = [t.strip() for t in payload.user_tags if t.strip()]
        garment.user_tags = json.dumps(cleaned)

    if payload.user_notes is not None:
        garment.user_notes = payload.user_notes

    db.commit()
    db.refresh(garment)
    return GarmentResponse.from_db(garment)
