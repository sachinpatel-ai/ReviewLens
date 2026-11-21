from tests.conftest import CSV_OK, upload


def test_health_and_root(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_upload_ok(client):
    r = upload(client)
    assert r.status_code == 201
    body = r.json()
    assert body["total_rows"] == 5
    assert body["counts"] == {"pending": 3, "analyzed": 0, "failed": 0, "skipped_empty": 1, "skipped_duplicate": 1}


def test_upload_rejects_non_csv(client):
    assert upload(client, "a,b", "notes.txt").status_code == 400


def test_upload_rejects_empty_file(client):
    r = upload(client, "")
    assert r.status_code == 400 and "empty" in r.json()["detail"]


def test_upload_rejects_missing_columns(client):
    r = upload(client, "review_id,product\n1,P\n")
    assert r.status_code == 422 and "rating" in r.json()["detail"]


def test_upload_rejects_binary_garbage(client):
    assert upload(client, b"\x00\x01\x02\xff\xfe" * 10).status_code in (400, 422)


def test_analyze_requires_api_key(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "gemini_api_key", "")
    bid = upload(client).json()["id"]
    assert client.post(f"/api/batches/{bid}/analyze").status_code == 503


def test_analyze_unknown_batch(client, fake_ai):
    assert client.post("/api/batches/999/analyze").status_code == 404


def test_full_flow_and_analytics_numbers(client, fake_ai):
    bid = upload(client).json()["id"]
    assert client.post(f"/api/batches/{bid}/analyze").status_code == 202

    batch = client.get(f"/api/batches/{bid}").json()
    assert batch["status"] == "completed"
    assert batch["counts"]["analyzed"] == 3

    a = client.get("/api/analytics").json()
    assert a["batch_id"] == bid
    assert a["total_reviews"] == 5
    assert (a["positive"], a["negative"], a["neutral"]) == (2, 1, 0)
    assert a["average_sentiment_score"] == 20.0  # (70 - 80 + 70) / 3 = 20
    assert a["average_rating"] == 3.0            # valid ratings of usable reviews: 5, 1 -> 3.0
    assert a["rating_distribution"] == {"1": 1, "2": 0, "3": 0, "4": 0, "5": 1}
    assert a["category_distribution"] == {"Product Quality": 3}
    assert a["negative_themes"][0] == {"theme": "breaks easily", "count": 1}
    assert a["data_quality"]["empty_review"] == 1 and a["data_quality"]["duplicate_review"] == 1
    assert a["data_quality"]["invalid_rating"] == 1
    assert a["insights"]["overall_summary"] == "Fake overall."


def test_cache_reuses_identical_text_across_batches(client, fake_ai):
    b1 = upload(client).json()["id"]
    client.post(f"/api/batches/{b1}/analyze")
    calls_after_first = fake_ai.calls
    b2 = upload(client).json()["id"]
    client.post(f"/api/batches/{b2}/analyze")
    assert fake_ai.calls == calls_after_first  # nothing new sent to the AI
    assert client.get(f"/api/batches/{b2}").json()["counts"]["analyzed"] == 3


def test_reviews_filters_search_sort(client, fake_ai):
    bid = upload(client).json()["id"]
    client.post(f"/api/batches/{bid}/analyze")

    all_ = client.get("/api/reviews").json()
    assert all_["total"] == 5

    neg = client.get("/api/reviews", params={"sentiment": "Negative"}).json()
    assert neg["total"] == 1 and neg["items"][0]["source_review_id"] == "2"

    assert client.get("/api/reviews", params={"rating": 5}).json()["total"] == 1
    assert client.get("/api/reviews", params={"search": "another"}).json()["total"] == 1
    assert client.get("/api/reviews", params={"status": "skipped_empty"}).json()["total"] == 1
    assert client.get("/api/reviews", params={"category": "Product Quality"}).json()["total"] == 3

    ordered = client.get("/api/reviews", params={"sort": "rating", "order": "desc"}).json()["items"]
    ratings = [r["rating"] for r in ordered if r["rating"] is not None]
    assert ratings == sorted(ratings, reverse=True)


def test_reviews_bad_params_rejected(client):
    assert client.get("/api/reviews", params={"sentiment": "Happy"}).status_code == 422
    assert client.get("/api/reviews", params={"sort": "password"}).status_code == 422
    assert client.get("/api/reviews", params={"page_size": 5000}).status_code == 422


def test_review_detail_and_404(client, fake_ai):
    bid = upload(client).json()["id"]
    client.post(f"/api/batches/{bid}/analyze")
    first = client.get("/api/reviews").json()["items"][0]
    detail = client.get(f"/api/reviews/{first['id']}")
    assert detail.status_code == 200 and detail.json()["summary"] == "Fake summary."
    assert client.get("/api/reviews/99999").status_code == 404


def test_rating_mismatch_flag(client, fake_ai):
    csv = "review_id,product,rating,date,review_text\n1,P,5,2025-01-01,Terrible it broke\n"
    bid = upload(client, csv).json()["id"]
    client.post(f"/api/batches/{bid}/analyze")
    assert client.get("/api/reviews").json()["items"][0]["rating_mismatch"] is True
    assert client.get("/api/analytics").json()["rating_sentiment_mismatches"] == 1


def test_analytics_empty_database(client):
    a = client.get("/api/analytics").json()
    assert a["total_reviews"] == 0 and a["average_rating"] is None and a["insights"] is None
    assert client.get("/api/reviews").json() == {"items": [], "total": 0, "page": 1, "page_size": 25}


def test_analytics_unknown_batch(client):
    assert client.get("/api/analytics", params={"batch_id": 42}).status_code == 404


def test_ai_failure_marks_reviews_failed_not_crash(client, monkeypatch):
    from app.config import settings
    from app.services import analysis_runner

    class Broken:
        def analyze_reviews(self, items):
            return {}, {i: "AI request failed" for i, _ in items}

        def generate_insights(self, stats):
            return None

    monkeypatch.setattr(settings, "gemini_api_key", "k")
    monkeypatch.setattr(analysis_runner, "make_analyzer", lambda: Broken())
    bid = upload(client).json()["id"]
    client.post(f"/api/batches/{bid}/analyze")
    b = client.get(f"/api/batches/{bid}").json()
    assert b["status"] == "failed" and b["counts"]["failed"] == 3 and b["error"]
