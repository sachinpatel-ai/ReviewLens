export const SENTIMENT_COLORS = { Positive: "#2E7D4F", Neutral: "#B58A1B", Negative: "#C0392B" };

export const STATUS_LABELS = {
  pending: "Waiting for analysis",
  analyzed: "Analyzed",
  failed: "Failed",
  skipped_empty: "Skipped (empty)",
  skipped_duplicate: "Skipped (duplicate)",
};

export const ISSUE_LABELS = {
  missing_rating: "Missing rating",
  invalid_rating: "Invalid rating",
  missing_date: "Missing date",
  invalid_date: "Invalid date",
  empty_review: "Empty review",
  duplicate_review: "Duplicate review",
  duplicate_review_id: "Duplicate review ID",
  missing_review_id: "Missing review ID",
  html_cleaned: "HTML removed",
  emoji_only: "Emoji only",
  long_review: "Very long review",
  possible_prompt_injection: "Contains instruction-like text",
};

export const fmtNumber = (n, digits = 1) => (n === null || n === undefined ? "–" : Number(n).toFixed(digits));
export const fmtDate = (d) => (d ? new Date(d).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "–");
