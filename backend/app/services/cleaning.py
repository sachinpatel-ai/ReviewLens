"""CSV validation and cleaning.

Key idea: we never silently drop rows. Bad rows are kept and *flagged* so the
dashboard can report data quality honestly.
"""
import hashlib
import html
import io
import math
import re
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

REQUIRED_COLUMNS = ["review_id", "product", "rating", "date", "review_text"]

_SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_INJECTION_RE = re.compile(
    r"(ignore\s+(all\s+)?(the\s+)?(previous|prior|above|earlier)\s+(instructions|rules|prompts?)"
    r"|disregard\s+.{0,40}(instructions|rules)"
    r"|system\s+prompt|you\s+are\s+now|new\s+instructions"
    r"|(mark|classify|label|rate)\s+(this|it)(\s+review)?\s+as\s+(positive|negative|neutral)"
    r"|override\s+(the\s+)?(rules|analysis))",
    re.I,
)


class CSVValidationError(Exception):
    """Raised for problems with the uploaded file as a whole. Message is user-safe."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class CleanedReview:
    source_review_id: str
    product: str
    raw_rating: str
    rating: Optional[int]
    review_date: Optional[str]
    raw_text: str
    clean_text: str
    text_hash: str
    is_duplicate: bool = False
    issues: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.clean_text:
            return "skipped_empty"
        if self.is_duplicate:
            return "skipped_duplicate"
        return "pending"


def normalize_column(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def clean_text(raw) -> str:
    """Decode entities, strip HTML, remove control chars, collapse whitespace."""
    if raw is None:
        return ""
    text = html.unescape(str(raw))
    text = _SCRIPT_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = _CTRL_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_rating(value) -> tuple[Optional[int], Optional[str]]:
    """Return (rating, issue). Only whole numbers 1-5 are valid."""
    s = str(value).strip() if value is not None else ""
    if s == "" or s.lower() in {"nan", "null", "none", "n/a"}:
        return None, "missing_rating"
    try:
        num = float(s)
    except ValueError:
        return None, "invalid_rating"
    if not math.isfinite(num) or num != int(num) or not 1 <= num <= 5:
        return None, "invalid_rating"
    return int(num), None


def parse_date(value) -> tuple[Optional[str], Optional[str]]:
    s = str(value).strip() if value is not None else ""
    if not s:
        return None, "missing_date"
    parsed = pd.to_datetime(s, errors="coerce")
    if pd.isna(parsed):
        return None, "invalid_date"
    return parsed.date().isoformat(), None


def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.lower().encode("utf-8")).hexdigest()


def read_csv_bytes(content: bytes, max_bytes: int, max_rows: int) -> pd.DataFrame:
    """Parse and validate the uploaded file. Raises CSVValidationError."""
    if not content or not content.strip():
        raise CSVValidationError("The uploaded file is empty.")
    if len(content) > max_bytes:
        raise CSVValidationError(
            f"File is too large. Maximum size is {max_bytes // (1024 * 1024)} MB.", 413
        )
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    try:
        df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    except pd.errors.EmptyDataError:
        raise CSVValidationError("The uploaded file is empty.")
    except (pd.errors.ParserError, ValueError) as exc:
        raise CSVValidationError(f"The file could not be read as a CSV: {str(exc)[:150]}")

    df.columns = [normalize_column(c) for c in df.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise CSVValidationError(
            f"Missing required column(s): {', '.join(missing)}. "
            f"Expected: {', '.join(REQUIRED_COLUMNS)}.",
            422,
        )
    if len(df) == 0:
        raise CSVValidationError("The CSV has headers but no review rows.", 422)
    if len(df) > max_rows:
        raise CSVValidationError(f"Too many rows ({len(df)}). Maximum is {max_rows}.", 413)
    return df


def clean_dataframe(df: pd.DataFrame) -> list[CleanedReview]:
    """Turn raw rows into CleanedReview objects with quality flags."""
    results: list[CleanedReview] = []
    seen_texts: set[tuple[str, str]] = set()
    seen_ids: set[str] = set()

    for _, row in df.iterrows():
        raw_text = str(row.get("review_text", ""))
        cleaned = clean_text(raw_text)
        rating, rating_issue = parse_rating(row.get("rating"))
        review_date, date_issue = parse_date(row.get("date"))
        source_id = str(row.get("review_id", "")).strip()
        product = clean_text(row.get("product", "")) or "Unknown product"

        issues: list[str] = [i for i in (rating_issue, date_issue) if i]
        if not cleaned:
            issues.append("empty_review")
        if raw_text != cleaned and cleaned and (_TAG_RE.search(html.unescape(raw_text)) or "&" in raw_text):
            issues.append("html_cleaned")
        if cleaned and not any(ch.isalnum() for ch in cleaned):
            issues.append("emoji_only")
        if len(cleaned) > 2000:
            issues.append("long_review")
        if _INJECTION_RE.search(cleaned):
            issues.append("possible_prompt_injection")
        if not source_id:
            issues.append("missing_review_id")
        elif source_id in seen_ids:
            issues.append("duplicate_review_id")
        seen_ids.add(source_id)

        is_dup = False
        if cleaned:
            key = (product.lower(), cleaned.lower())
            if key in seen_texts:
                is_dup = True
                issues.append("duplicate_review")
            seen_texts.add(key)

        results.append(
            CleanedReview(
                source_review_id=source_id,
                product=product,
                raw_rating=str(row.get("rating", "")).strip(),
                rating=rating,
                review_date=review_date,
                raw_text=raw_text,
                clean_text=cleaned,
                text_hash=text_fingerprint(cleaned),
                is_duplicate=is_dup,
                issues=issues,
            )
        )
    return results
