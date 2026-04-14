import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.garment import Garment
from ..schemas.garment import GarmentResponse
from ..services import classifier, export as export_svc, storage

router = APIRouter(prefix="/api/garments", tags=["garments"])


@router.post("/upload", response_model=List[GarmentResponse])
async def upload_garments(
    files: List[UploadFile] = File(...),
    designer: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload one or more garment images. Each file is classified by Claude and
    the results are stored. Returns a list of created garment records.
    """
    results = []
    for file in files:
        try:
            filename, abs_path = storage.save_upload(file.file, file.filename or "upload.jpg")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        try:
            attrs = classifier.classify_image(abs_path)
        except Exception as exc:
            storage.delete_file(filename)
            raise HTTPException(status_code=422, detail=f"Classification failed: {exc}")

        garment = Garment(
            id=str(uuid.uuid4()),
            file_path=filename,
            original_filename=file.filename or filename,
            uploaded_at=datetime.now(timezone.utc),
            designer=designer or None,
            description=attrs.get("description"),
            garment_type=attrs.get("garment_type"),
            style=attrs.get("style"),
            material=attrs.get("material"),
            color_palette=json.dumps(attrs.get("color_palette") or []),
            pattern=attrs.get("pattern"),
            season=attrs.get("season"),
            occasion=attrs.get("occasion"),
            consumer_profile=attrs.get("consumer_profile"),
            trend_notes=attrs.get("trend_notes"),
            location_context=attrs.get("location_context"),
            continent=attrs.get("continent"),
            country=attrs.get("country"),
            city=attrs.get("city"),
            year=attrs.get("year"),
            month=attrs.get("month"),
            confidence=json.dumps(attrs.get("confidence") or {}),
        )
        db.add(garment)
        db.commit()
        db.refresh(garment)
        results.append(GarmentResponse.from_db(garment))

    return results


@router.get("/export", response_class=StreamingResponse)
def export_csv(db: Session = Depends(get_db)):
    """Download the full library as a CSV file."""
    garments = db.query(Garment).order_by(Garment.uploaded_at.desc()).all()
    csv_data = export_svc.to_csv(garments)
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fashion_library.csv"},
    )


@router.get("/{garment_id}", response_model=GarmentResponse)
def get_garment(garment_id: str, db: Session = Depends(get_db)):
    garment = db.query(Garment).filter(Garment.id == garment_id).first()
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")
    return GarmentResponse.from_db(garment)


@router.delete("/{garment_id}")
def delete_garment(garment_id: str, db: Session = Depends(get_db)):
    garment = db.query(Garment).filter(Garment.id == garment_id).first()
    if not garment:
        raise HTTPException(status_code=404, detail="Garment not found")
    storage.delete_file(garment.file_path)
    db.delete(garment)
    db.commit()
    return {"ok": True}


@router.get("/{garment_id}/similar", response_model=List[GarmentResponse])
def similar_garments(garment_id: str, db: Session = Depends(get_db)):
    """
    Find other garments that share the same garment_type and style as the
    given item. Simple but effective for a POC — a production version would
    use embedding similarity.
    """
    source = db.query(Garment).filter(Garment.id == garment_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Garment not found")

    query = db.query(Garment).filter(Garment.id != garment_id)
    if source.garment_type:
        query = query.filter(Garment.garment_type == source.garment_type)
    if source.style:
        query = query.filter(Garment.style == source.style)

    results = query.limit(8).all()
    return [GarmentResponse.from_db(g) for g in results]
