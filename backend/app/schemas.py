"""Pydantic schemas for API responses."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StatusCounts(BaseModel):
    pending: int = 0
    analyzed: int = 0
    failed: int = 0
    skipped_empty: int = 0
    skipped_duplicate: int = 0


class BatchOut(BaseModel):
    id: int
    filename: str
    status: str
    total_rows: int
    created_at: datetime
    error: Optional[str] = None
    counts: StatusCounts


class ReviewOut(BaseModel):
    id: int
    batch_id: int
    source_review_id: Optional[str]
    product: Optional[str]
    rating: Optional[int]
    raw_rating: Optional[str]
    review_date: Optional[str]
    raw_text: Optional[str]
    clean_text: Optional[str]
    data_issues: list[str]
    status: str
    error: Optional[str]
    sentiment: Optional[str]
    sentiment_score: Optional[int]
    category: Optional[str]
    summary: Optional[str]
    key_issues: list[str]
    key_positives: list[str]
    rating_mismatch: bool


class ReviewPage(BaseModel):
    items: list[ReviewOut]
    total: int
    page: int
    page_size: int


class ThemeCount(BaseModel):
    theme: str
    count: int


class Insights(BaseModel):
    overall_summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]


class AnalyticsOut(BaseModel):
    batch_id: Optional[int]
    total_reviews: int
    analyzed_reviews: int
    positive: int
    negative: int
    neutral: int
    average_rating: Optional[float]
    average_sentiment_score: Optional[float]
    sentiment_distribution: dict[str, int]
    rating_distribution: dict[str, int]
    category_distribution: dict[str, int]
    positive_themes: list[ThemeCount]
    negative_themes: list[ThemeCount]
    rating_sentiment_mismatches: int
    data_quality: dict[str, int]
    insights: Optional[Insights] = None
