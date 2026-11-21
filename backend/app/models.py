"""Database tables."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Batch(Base):
    """One CSV upload."""

    __tablename__ = "batches"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    total_rows = Column(Integer, default=0)
    status = Column(String(30), default="uploaded")  # uploaded | analyzing | completed | failed
    error = Column(Text, nullable=True)
    insights_json = Column(Text, nullable=True)  # AI product summary + recommendations

    reviews = relationship("Review", back_populates="batch", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), index=True, nullable=False)

    # original + cleaned data
    source_review_id = Column(String(100))
    product = Column(String(255))
    raw_rating = Column(String(50))
    rating = Column(Integer, nullable=True)  # None when missing/invalid
    review_date = Column(String(20), nullable=True)  # ISO date
    raw_text = Column(Text)
    clean_text = Column(Text)
    text_hash = Column(String(64), index=True)
    data_issues = Column(String(255), default="")  # comma-separated flags
    is_duplicate = Column(Boolean, default=False)

    # AI results
    sentiment = Column(String(20), nullable=True)
    sentiment_score = Column(Integer, nullable=True)
    category = Column(String(50), nullable=True)
    summary = Column(Text, nullable=True)
    key_issues = Column(Text, default="[]")  # JSON list
    key_positives = Column(Text, default="[]")  # JSON list

    # pending | analyzed | failed | skipped_empty | skipped_duplicate
    status = Column(String(30), default="pending", index=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    batch = relationship("Batch", back_populates="reviews")
