from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Batch
from app.schemas import AnalyticsOut
from app.services.analytics_service import compute_analytics, resolve_batch_id

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsOut)
def get_analytics(batch_id: Optional[int] = None, db: Session = Depends(get_db)):
    if batch_id is not None and not db.get(Batch, batch_id):
        raise HTTPException(404, "Batch not found.")
    return compute_analytics(db, resolve_batch_id(db, batch_id))
