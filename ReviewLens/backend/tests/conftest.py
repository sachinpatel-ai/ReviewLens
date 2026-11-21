import json
import os

# Must be set BEFORE the app is imported, so tests never touch the real database.
os.environ["DATABASE_URL"] = "sqlite:///./test_reviewlens.db"
os.environ["GEMINI_API_KEY"] = ""
os.environ["RETRY_BASE_DELAY"] = "0"

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import Base, engine
from app.main import app
from app.services import analysis_runner
from app.services.ai_service import InsightsResult, ReviewAnalysis


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


class FakeAnalyzer:
    """Stands in for Gemini. Deterministic: 'bad'/'broke' -> Negative, else Positive."""

    calls = 0

    def analyze_reviews(self, items):
        FakeAnalyzer.calls += 1
        results = {}
        for idx, text in items:
            neg = any(w in text.lower() for w in ("bad", "broke", "terrible"))
            results[idx] = ReviewAnalysis(
                index=idx,
                sentiment="Negative" if neg else "Positive",
                sentiment_score=-80 if neg else 70,
                category="Product Quality",
                summary="Fake summary.",
                key_issues=["breaks easily"] if neg else [],
                key_positives=[] if neg else ["great sound"],
            )
        return results, {}

    def generate_insights(self, stats):
        return InsightsResult(
            overall_summary="Fake overall.", strengths=["sound"], weaknesses=["durability"],
            recommendations=["Improve durability"],
        )


@pytest.fixture()
def fake_ai(monkeypatch):
    FakeAnalyzer.calls = 0
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(analysis_runner, "make_analyzer", lambda: FakeAnalyzer())
    return FakeAnalyzer


CSV_OK = (
    "review_id,product,rating,date,review_text\n"
    "1,Buds,5,2025-01-01,Great sound\n"
    "2,Buds,1,2025-01-02,Terrible they broke\n"
    "3,Buds,4,2025-01-03,Great sound\n"      # duplicate of 1 -> skipped
    "4,Buds,3,2025-01-04,\n"                  # empty -> skipped
    "5,Buds,9,2025-01-05,Another good one\n"  # invalid rating
)


def upload(client, content=CSV_OK, name="reviews.csv"):
    data = content.encode() if isinstance(content, str) else content
    return client.post("/api/upload", files={"file": (name, data, "text/csv")})
