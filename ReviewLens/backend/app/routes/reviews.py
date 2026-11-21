"""List / search / filter / view reviews."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Review
from app.schemas import ReviewOut, ReviewPage
from app.services.analytics_service import rating_mismatch, resolve_batch_id

router = APIRouter(prefix="/api", tags=["reviews"])

SORT_COLUMNS = {
    "date": Review.review_date, "rating": Review.rating, "sentiment_score": Review.sentiment_score,
    "product": Review.product, "id": Review.id,
}


def _json_list(value) -> list[str]:
    try:
        data = json.loads(value or "[]")
        return [str(x) for x in data] if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def review_to_out(r: Review) -> ReviewOut:
    return ReviewOut(
        id=r.id, batch_id=r.batch_id, source_review_id=r.source_review_id, product=r.product,
        rating=r.rating, raw_rating=r.raw_rating, review_date=r.review_date, raw_text=r.raw_text,
        clean_text=r.clean_text, data_issues=[i for i in (r.data_issues or "").split(",") if i],
        status=r.status, error=r.error, sentiment=r.sentiment, sentiment_score=r.sentiment_score,
        category=r.category, summary=r.summary, key_issues=_json_list(r.key_issues),
        key_positives=_json_list(r.key_positives), rating_mismatch=rating_mismatch(r.rating, r.sentiment),
    )


@router.get("/reviews", response_model=ReviewPage)
def list_reviews(
    batch_id: int | None = None,
    search: str | None = Query(None, max_length=100),
    sentiment: str | None = Query(None, pattern="^(Positive|Negative|Neutral)$"),
    rating: int | None = Query(None, ge=1, le=5),
    category: str | None = None,
    status: str | None = None,
    sort: str = Query("id", pattern="^(date|rating|sentiment_score|product|id)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    bid = resolve_batch_id(db, batch_id)
    if bid is None:
        return ReviewPage(items=[], total=0, page=page, page_size=page_size)

    q = db.query(Review).filter(Review.batch_id == bid)
    if search:
        like = f"%{search.strip()}%"
        q = q.filter(or_(Review.clean_text.ilike(like), Review.summary.ilike(like), Review.product.ilike(like)))
    if sentiment:
        q = q.filter(Review.sentiment == sentiment)
    if rating:
        q = q.filter(Review.rating == rating)
    if category:
        q = q.filter(Review.category == category)
    if status:
        q = q.filter(Review.status == status)

    total = q.count()
    col = SORT_COLUMNS[sort]
    q = q.order_by(col.desc() if order == "desc" else col.asc(), Review.id.asc())
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return ReviewPage(items=[review_to_out(r) for r in items], total=total, page=page, page_size=page_size)


@router.get("/reviews/{review_id}", response_model=ReviewOut)
def get_review(review_id: int, db: Session = Depends(get_db)):
    r = db.get(Review, review_id)
    if not r:
        raise HTTPException(404, "Review not found.")
    return review_to_out(r)
