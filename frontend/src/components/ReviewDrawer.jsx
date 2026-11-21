import { useEffect } from "react";
import { AlertTriangle, X } from "lucide-react";
import { SentimentBadge } from "./ui";
import { fmtDate, ISSUE_LABELS, STATUS_LABELS } from "../utils/format";

export default function ReviewDrawer({ review, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const r = review;
  return (
    <div className="overlay" onClick={onClose}>
      <aside className="drawer" role="dialog" aria-label="Review details" onClick={(e) => e.stopPropagation()}>
        <div className="card-head">
          <div>
            <h2>{r.product}</h2>
            <p className="muted">Review {r.source_review_id || "–"} · {fmtDate(r.review_date)}</p>
          </div>
          <button className="btn" onClick={onClose} aria-label="Close"><X size={16} /></button>
        </div>

        <div className="compare">
          <div>
            <h3>Star rating</h3>
            <div className="big">{r.rating ? `${r.rating} / 5` : "–"}</div>
            {!r.rating && <p className="muted">Original value: “{r.raw_rating || "blank"}”</p>}
          </div>
          <div>
            <h3>Detected sentiment</h3>
            <div className="big"><SentimentBadge sentiment={r.sentiment} /></div>
            {r.sentiment_score !== null && <p className="muted">Score {r.sentiment_score} (−100 to +100)</p>}
          </div>
        </div>

        {r.rating_mismatch && (
          <div className="banner warn">
            <AlertTriangle size={18} />
            <p className="grow">The star rating and the review text disagree. The sentiment above is based on the text.</p>
          </div>
        )}

        <div><h3>Review</h3><div className="quote">{r.clean_text || <span className="muted">(empty)</span>}</div></div>
        {r.summary && <div><h3>AI summary</h3><p>{r.summary}</p></div>}
        {r.category && <div><h3>Category</h3><span className="badge accent">{r.category}</span></div>}
        {r.key_issues.length > 0 && <div><h3>Issues mentioned</h3><div className="chips">{r.key_issues.map((k) => <span key={k} className="badge Negative">{k}</span>)}</div></div>}
        {r.key_positives.length > 0 && <div><h3>Positives mentioned</h3><div className="chips">{r.key_positives.map((k) => <span key={k} className="badge Positive">{k}</span>)}</div></div>}

        <div>
          <h3>Processing</h3>
          <div className="chips">
            <span className="badge plain">{STATUS_LABELS[r.status] || r.status}</span>
            {r.data_issues.map((i) => <span key={i} className="badge warn">{ISSUE_LABELS[i] || i}</span>)}
          </div>
          {r.error && <p className="muted" style={{ marginTop: 8 }}>Error: {r.error}</p>}
        </div>
      </aside>
    </div>
  );
}
