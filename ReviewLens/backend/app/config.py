"""Central settings, read from environment variables (.env in development)."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.database_url: str = os.getenv("DATABASE_URL", "sqlite:///./reviewlens.db")
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]
        self.max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "2"))
        self.max_rows: int = int(os.getenv("MAX_ROWS", "500"))
        self.ai_batch_size: int = int(os.getenv("AI_BATCH_SIZE", "10"))
        self.max_review_chars: int = 2000  # longer reviews are truncated before going to the AI
        self.retry_base_delay: float = float(os.getenv("RETRY_BASE_DELAY", "2"))


settings = Settings()
