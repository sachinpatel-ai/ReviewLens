"""Upload a CSV, start analysis, check batch progress."""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Batch, Review
from app.schemas import BatchOut, StatusCounts
from app.services import ai_service
from app.services.analysis_runner import run_analysis
from app.services.cleaning import CSVValidationError, clean_dataframe, read_csv_bytes

router = APIRouter(prefix="/api", tags=["batches"])


def batch_to_out(db: Session, batch: Batch) -> BatchOut:
    rows = (
        db.query(Review.status, func.count(Review.id))
        .filter(Review.batch_id == batch.id)
        .group_by(Review.status)
        .all()
    )
    return BatchOut(
        id=batch.id, filename=batch.filename, status=batch.status, total_rows=batch.total_rows or 0,
        created_at=batch.created_at, error=batch.error, counts=StatusCounts(**{s: c for s, c in rows}),
    )


@router.post("/upload", response_model=BatchOut, status_code=201)
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, "Only .csv files are accepted.")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await file.read(max_bytes + 1)
    try:
        df = read_csv_bytes(content, max_bytes, settings.max_rows)
        cleaned = clean_dataframe(df)
    except CSVValidationError as exc:
        raise HTTPException(exc.status_code, exc.message)

    batch = Batch(filename=file.filename[:255], total_rows=len(cleaned), status="uploaded")
    db.add(batch)
    db.flush()
    db.add_all(
        Review(
            batch_id=batch.id, source_review_id=c.source_review_id, product=c.product,
            raw_rating=c.raw_rating, rating=c.rating, review_date=c.review_date,
            raw_text=c.raw_text, clean_text=c.clean_text, text_hash=c.text_hash,
            data_issues=",".join(c.issues), is_duplicate=c.is_duplicate, status=c.status,
        )
        for c in cleaned
    )
    db.commit()
    return batch_to_out(db, batch)


@router.post("/batches/{batch_id}/analyze", response_model=BatchOut, status_code=202)
def analyze_batch(batch_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found.")
    if batch.status == "analyzing":
        raise HTTPException(409, "This batch is already being analyzed.")
    if not ai_service.is_configured():
        raise HTTPException(503, "GEMINI_API_KEY is not configured on the server.")
    batch.status = "analyzing"
    db.commit()
    background.add_task(run_analysis, batch_id)
    return batch_to_out(db, batch)


@router.get("/batches", response_model=list[BatchOut])
def list_batches(db: Session = Depends(get_db)):
    batches = db.query(Batch).order_by(Batch.id.desc()).limit(50).all()
    return [batch_to_out(db, b) for b in batches]


@router.get("/batches/{batch_id}", response_model=BatchOut)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(404, "Batch not found.")
    return batch_to_out(db, batch)
