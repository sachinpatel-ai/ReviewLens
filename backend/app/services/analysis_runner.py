"""Runs AI analysis for a batch: cache reuse, chunked AI calls, saving results."""
import json
import logging

from app.config import settings
from app.database import SessionLocal
from app.models import Batch, Review
from app.services.ai_service import GeminiAnalyzer
from app.services.analytics_service import build_insight_input

logger = logging.getLogger("reviewlens.runner")


def make_analyzer():
    return GeminiAnalyzer()


def _apply_result(review: Review, res) -> None:
    review.sentiment = res.sentiment
    review.sentiment_score = res.sentiment_score
    review.category = res.category
    review.summary = res.summary
    review.key_issues = json.dumps(res.key_issues)
    review.key_positives = json.dumps(res.key_positives)
    review.status = "analyzed"
    review.error = None


def run_analysis(batch_id: int, session_factory=SessionLocal) -> None:
    db = session_factory()
    try:
        batch = db.get(Batch, batch_id)
        if batch is None:
            return
        batch.status = "analyzing"
        batch.error = None
        db.commit()

        todo = (
            db.query(Review)
            .filter(Review.batch_id == batch_id, Review.status.in_(["pending", "failed"]))
            .all()
        )

        # 1) Reuse cached results for identical text (saves API calls)
        remaining = []
        for r in todo:
            cached = (
                db.query(Review)
                .filter(Review.text_hash == r.text_hash, Review.status == "analyzed", Review.id != r.id)
                .first()
            )
            if cached:
                for f in ("sentiment", "sentiment_score", "category", "summary", "key_issues", "key_positives"):
                    setattr(r, f, getattr(cached, f))
                r.status, r.error = "analyzed", None
            else:
                remaining.append(r)
        db.commit()

        # 2) Ask the AI, in small chunks
        analyzer = make_analyzer()
        size = settings.ai_batch_size
        for start in range(0, len(remaining), size):
            chunk = remaining[start : start + size]
            items = [(r.id, r.clean_text) for r in chunk]
            results, errors = analyzer.analyze_reviews(items)
            for r in chunk:
                if r.id in results:
                    _apply_result(r, results[r.id])
                else:
                    r.status = "failed"
                    r.error = errors.get(r.id, "Unknown analysis error.")
            db.commit()  # commit per chunk so the UI can show progress

        # 3) Overall insights (one extra AI call)
        analyzed = db.query(Review).filter(Review.batch_id == batch_id, Review.status == "analyzed").count()
        failed = db.query(Review).filter(Review.batch_id == batch_id, Review.status == "failed").count()
        if analyzed:
            insights = analyzer.generate_insights(build_insight_input(db, batch_id))
            batch.insights_json = insights.model_dump_json() if insights else None
        if analyzed == 0 and failed:
            batch.status = "failed"
            batch.error = "No reviews could be analyzed. Check the AI key, quota and try again."
        else:
            batch.status = "completed"
            if failed:
                batch.error = f"{failed} review(s) failed analysis. Run analysis again to retry them."
        db.commit()
    except Exception as exc:  # never leave a batch stuck on "analyzing"
        logger.exception("Analysis crashed")
        db.rollback()
        batch = db.get(Batch, batch_id)
        if batch:
            batch.status = "failed"
            batch.error = f"Analysis crashed: {str(exc)[:200]}"
            db.commit()
    finally:
        db.close()
