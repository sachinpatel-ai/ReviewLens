"""All dashboard numbers are computed here from real database rows."""
import json
import re
from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Batch, Review
from app.schemas import AnalyticsOut, Insights, ThemeCount

QUALITY_FLAGS = [
    "empty_review", "duplicate_review", "missing_rating", "invalid_rating",
    "invalid_date", "emoji_only", "possible_prompt_injection", "html_cleaned",
]


def rating_mismatch(rating: Optional[int], sentiment: Optional[str]) -> bool:
    if rating is None or sentiment is None:
        return False
    return (rating >= 4 and sentiment == "Negative") or (rating <= 2 and sentiment == "Positive")


def _norm_theme(t: str) -> str:
    return re.sub(r"\s+", " ", t.lower()).strip()


def _themes(reviews: list[Review], attr: str, limit: int = 8) -> list[ThemeCount]:
    counter: Counter = Counter()
    for r in reviews:
        try:
            for t in json.loads(getattr(r, attr) or "[]"):
                if _norm_theme(t):
                    counter[_norm_theme(t)] += 1
        except json.JSONDecodeError:
            continue
    return [ThemeCount(theme=t, count=c) for t, c in counter.most_common(limit)]


def resolve_batch_id(db: Session, batch_id: Optional[int]) -> Optional[int]:
    if batch_id is not None:
        return batch_id
    latest = db.query(Batch).order_by(Batch.id.desc()).first()
    return latest.id if latest else None


def compute_analytics(db: Session, batch_id: Optional[int]) -> AnalyticsOut:
    batch = db.get(Batch, batch_id) if batch_id is not None else None
    reviews = db.query(Review).filter(Review.batch_id == batch_id).all() if batch else []

    usable = [r for r in reviews if r.status not in ("skipped_empty", "skipped_duplicate")]
    analyzed = [r for r in reviews if r.status == "analyzed"]

    sent = Counter(r.sentiment for r in analyzed)
    rated = [r.rating for r in usable if r.rating is not None]
    scores = [r.sentiment_score for r in analyzed if r.sentiment_score is not None]

    quality = {"total_rows": len(reviews), "usable_reviews": len(usable)}
    for flag in QUALITY_FLAGS:
        quality[flag] = sum(1 for r in reviews if flag in (r.data_issues or "").split(","))

    insights = None
    if batch and batch.insights_json:
        try:
            insights = Insights.model_validate_json(batch.insights_json)
        except ValueError:
            insights = None

    return AnalyticsOut(
        batch_id=batch.id if batch else None,
        total_reviews=len(reviews),
        analyzed_reviews=len(analyzed),
        positive=sent.get("Positive", 0),
        negative=sent.get("Negative", 0),
        neutral=sent.get("Neutral", 0),
        average_rating=round(sum(rated) / len(rated), 2) if rated else None,
        average_sentiment_score=round(sum(scores) / len(scores), 1) if scores else None,
        sentiment_distribution={k: sent.get(k, 0) for k in ("Positive", "Neutral", "Negative")},
        rating_distribution={str(n): rated.count(n) for n in range(1, 6)},
        category_distribution=dict(Counter(r.category for r in analyzed if r.category).most_common()),
        positive_themes=_themes(analyzed, "key_positives"),
        negative_themes=_themes(analyzed, "key_issues"),
        rating_sentiment_mismatches=sum(1 for r in analyzed if rating_mismatch(r.rating, r.sentiment)),
        data_quality=quality,
        insights=insights,
    )


def build_insight_input(db: Session, batch_id: int) -> dict:
    """Compact, aggregated data sent to the AI for the overall summary."""
    a = compute_analytics(db, batch_id)
    sample = (
        db.query(Review.summary)
        .filter(Review.batch_id == batch_id, Review.status == "analyzed")
        .limit(15)
        .all()
    )
    return {
        "analyzed_reviews": a.analyzed_reviews,
        "sentiment_counts": a.sentiment_distribution,
        "average_rating": a.average_rating,
        "average_sentiment_score": a.average_sentiment_score,
        "categories": a.category_distribution,
        "top_complaints": [t.model_dump() for t in a.negative_themes],
        "top_praise": [t.model_dump() for t in a.positive_themes],
        "example_summaries": [s[0] for s in sample],
    }
