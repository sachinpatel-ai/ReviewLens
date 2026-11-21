from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import analytics, reviews, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ReviewLens API",
    description="AI-powered product review analysis.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(reviews.router)
app.include_router(analytics.router)


@app.get("/", tags=["system"])
def root():
    return {"name": "ReviewLens API", "docs": "/docs"}


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}
