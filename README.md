<<<<<<< HEAD
# ReviewLens – AI Review Insights

Upload a CSV of product reviews and get AI-powered sentiment, topics, complaints, strengths and recommendations on a clean dashboard.

**Stack:** FastAPI · Pydantic · SQLAlchemy + SQLite · Pandas · Google Gemini (`google-genai`) · React + Vite · Recharts · pytest + HTTPX

## How it works

```
CSV → validate & clean (Pandas) → SQLite → Gemini (chunks of 10, JSON) → validate (Pydantic) → SQLite → analytics → React dashboard
```

1. **Upload** (`POST /api/upload`): file type, size and columns are checked. Every row is cleaned (HTML removed, entities decoded, whitespace normalized, rating must be a whole number 1–5, dates parsed). Bad rows are **kept and flagged**, never silently dropped, so data quality can be reported. Empty rows and duplicates are stored but skipped for AI.
2. **Analyze** (`POST /api/batches/{id}/analyze`): runs as a background task. Identical review text already analyzed earlier is reused from the database (cache); the rest goes to Gemini in chunks of 10 (about 3 calls for 26 reviews, plus 1 call for the overall summary).
3. **Validate**: model output must be valid JSON matching a strict schema (sentiment label, score −100..100, known category, non-empty summary). Anything else is rejected, retried with backoff for rate limits and server errors, and finally marked `failed` with the reason.
4. **Dashboard**: all numbers are computed from database rows (`services/analytics_service.py`).

### Prompt-injection defence
- Rules live in the **system instruction**; reviews are sent only as escaped JSON data in the user message.
- The model is told review text is untrusted and must never be obeyed. Injection attempts are analysed as content and flagged in data quality.
- Output is schema-validated, so an injected instruction cannot change the format. If the numeric score and the label disagree, the score wins.
- Limits: no LLM defence is perfect. This reduces the risk, it does not eliminate it.

### Design decisions
- Sentiment comes from the **text**, not the stars. Rating/sentiment disagreements are flagged in the UI.
- Duplicate = same product + same text (case-insensitive) after cleaning. The first copy is analyzed.
- Average rating uses valid ratings of usable (non-empty, non-duplicate) reviews.
- Strengths/weaknesses come from the AI summary. If that call fails, the UI falls back to the most frequent themes and says so.

## Python version
Built and tested on **Python 3.15**: all 58 tests pass (verified on 3.15.0b4 with the pinned `requirements.txt`). Older pins fail on 3.15 because some packages have no 3.15 wheels, so do not downgrade the versions in `requirements.txt` unless you also change Python. Create the virtual environment with 3.15: `py -3.15 -m venv venv` (Windows) or `python3.15 -m venv venv` (Mac/Linux).

## Run locally

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   |   source venv/bin/activate   (Mac/Linux)
pip install -r requirements.txt
copy .env.example .env         # Mac/Linux: cp .env.example .env   then put your GEMINI_API_KEY in .env
uvicorn app.main:app --reload
```
Swagger docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
copy .env.example .env         # Mac/Linux: cp .env.example .env
npm run dev
```
Open http://localhost:5173 → **Upload CSV** → choose `backend/data/sample_reviews.csv` → **Run AI analysis**.

### Tests
```bash
cd backend
python -m pytest -q
```
Tests use a fake AI, so they need no API key and make no network calls.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/upload` | Upload + clean a CSV, creates a batch |
| POST | `/api/batches/{id}/analyze` | Start AI analysis (202, then poll the batch) |
| GET | `/api/batches`, `/api/batches/{id}` | Batch list / progress |
| GET | `/api/reviews` | Search, filter (sentiment, rating, category, status), sort, paginate |
| GET | `/api/reviews/{id}` | One review |
| GET | `/api/analytics?batch_id=` | Dashboard numbers (latest batch by default) |

## Deploy

### Backend → Render
1. Push this repo to GitHub.
2. Render → **New → Web Service** → pick the repo. Root Directory `backend`, Build `pip install -r requirements.txt`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, Health check path `/health`. (Or use the included `render.yaml` Blueprint.)
3. Environment variables: `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`, `PYTHON_VERSION=3.15.0 (see note below)`, `CORS_ORIGINS` (set after the frontend is deployed).
4. Copy the service URL, e.g. `https://reviewlens-api.onrender.com`.

### Frontend → Vercel
1. Vercel → **Add New Project** → same repo, Root Directory `frontend` (framework: Vite).
2. Environment variable `VITE_API_URL` = your Render URL (no trailing slash).
3. Deploy. Then in Render set `CORS_ORIGINS` to your Vercel URL and redeploy the backend.

### Known limitations
- Render must offer Python 3.15 for `PYTHON_VERSION`. If the build says the version is unavailable, check Render's supported-versions page and use the newest listed 3.x. The requirements are pinned for 3.15, so a lower version may need looser pins.
- Render's free tier sleeps when idle and its disk is **ephemeral**: the SQLite file resets on redeploy or restart. Fine for a demo; use Postgres via `DATABASE_URL` for real persistence.
- Analysis runs in an in-process background task. If the server restarts mid-run, run analysis again; unfinished reviews are picked up.
- No authentication: anyone with the URL can upload.
- The free Gemini tier is rate-limited; the app retries 429/5xx errors with backoff.
=======
# ReviewLens
>>>>>>> 191bf47bc278f557440771f3c475c5055919dc83
