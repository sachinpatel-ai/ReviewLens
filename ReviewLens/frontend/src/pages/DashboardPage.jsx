import { Activity, AlertTriangle, BarChart3, Frown, Meh, Play, Smile, Star, Upload } from "lucide-react";
import { CategoryBars, RatingBars, SentimentDonut, ThemeList } from "../components/Charts";
import { EmptyState, ErrorState, KpiCard, Loading } from "../components/ui";
import { fmtNumber, ISSUE_LABELS } from "../utils/format";

function StatusBanner({ batch, onRun, busy }) {
  if (!batch) return null;
  const c = batch.counts;
  const work = c.pending + c.analyzed + c.failed;
  if (batch.status === "uploaded")
    return (
      <div className="banner info">
        <Play size={18} />
        <p className="grow"><b>{work} reviews are ready for analysis.</b> Run the AI analysis to see sentiment, themes and recommendations.</p>
        <button className="btn primary" onClick={onRun} disabled={busy}>Run AI analysis</button>
      </div>
    );
  if (batch.status === "analyzing") {
    const pct = work ? Math.round(((c.analyzed + c.failed) / work) * 100) : 0;
    return (
      <div className="banner info" role="status">
        <div className="spinner" />
        <div className="grow"><b>Analyzing reviews… {c.analyzed} of {work} done.</b>
          <div className="progress"><div style={{ width: `${pct}%` }} /></div></div>
      </div>
    );
  }
  if (batch.error)
    return (
      <div className={`banner ${batch.status === "failed" ? "error" : "warn"}`}>
        <AlertTriangle size={18} />
        <p className="grow">{batch.error}</p>
        <button className="btn" onClick={onRun} disabled={busy}>Retry analysis</button>
      </div>
    );
  return null;
}

export default function DashboardPage({ analytics: a, current, loading, error, onRetry, onRun, busy, onNavigate }) {
  if (loading && !a) return <Loading label="Loading dashboard…" />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;
  if (!current || !a || a.total_reviews === 0)
    return (
      <EmptyState icon={Upload} title="No reviews yet" text="Upload a CSV of product reviews to see sentiment, themes and recommendations."
        action={<button className="btn primary" onClick={() => onNavigate("upload")}>Upload a CSV</button>} />
    );

  const ins = a.insights;
  const strengths = ins?.strengths?.length ? ins.strengths : a.positive_themes.slice(0, 4).map((t) => t.theme);
  const weaknesses = ins?.weaknesses?.length ? ins.weaknesses : a.negative_themes.slice(0, 4).map((t) => t.theme);
  const hasAI = a.analyzed_reviews > 0;
  const q = a.data_quality;

  return (
    <>
      <StatusBanner batch={current} onRun={onRun} busy={busy} />

      <section className="grid kpis" aria-label="Key numbers">
        <KpiCard icon={BarChart3} label="Total reviews" value={a.total_reviews} hint={`${a.analyzed_reviews} analyzed`} />
        <KpiCard icon={Smile} label="Positive" value={a.positive} tone="pos" />
        <KpiCard icon={Frown} label="Negative" value={a.negative} tone="neg" />
        <KpiCard icon={Meh} label="Neutral" value={a.neutral} tone="neu" />
        <KpiCard icon={Star} label="Avg rating" value={fmtNumber(a.average_rating, 2)} hint="valid ratings only" />
        <KpiCard icon={Activity} label="Avg sentiment" value={fmtNumber(a.average_sentiment_score)} hint="scale −100 to +100" />
      </section>

      {hasAI && (
        <>
          <section className="grid cols-3">
            <div className="card"><div className="card-head"><h2>Sentiment</h2></div><SentimentDonut distribution={a.sentiment_distribution} /></div>
            <div className="card"><div className="card-head"><h2>Star ratings</h2></div><RatingBars distribution={a.rating_distribution} /></div>
            <div className="card"><div className="card-head"><h2>Topics</h2></div><CategoryBars distribution={a.category_distribution} /></div>
          </section>

          <section className="grid cols-2">
            <div className="card"><div className="card-head"><h2>Most common complaints</h2></div><ThemeList themes={a.negative_themes} color="#c0392b" /></div>
            <div className="card"><div className="card-head"><h2>What customers like</h2></div><ThemeList themes={a.positive_themes} color="#2e7d4f" /></div>
          </section>

          <section className="card">
            <div className="card-head"><h2>AI product insights</h2>{a.rating_sentiment_mismatches > 0 && <span className="badge warn">{a.rating_sentiment_mismatches} rating/text mismatches</span>}</div>
            {ins ? <p style={{ marginBottom: 16 }}>{ins.overall_summary}</p> : <p className="muted" style={{ marginBottom: 16 }}>The AI summary could not be generated for this batch. Run the analysis again to retry. Strengths and weaknesses below come from the most frequent review themes.</p>}
            <div className="grid cols-3">
              <div><h3>Strengths</h3><ul className="plain">{strengths.length ? strengths.map((s) => <li key={s}>{s}</li>) : <li className="muted">None identified</li>}</ul></div>
              <div><h3>Weaknesses</h3><ul className="plain">{weaknesses.length ? weaknesses.map((s) => <li key={s}>{s}</li>) : <li className="muted">None identified</li>}</ul></div>
              <div><h3>Recommendations</h3><ul className="plain">{ins?.recommendations?.length ? ins.recommendations.map((s) => <li key={s}>{s}</li>) : <li className="muted">Available after a successful AI summary</li>}</ul></div>
            </div>
          </section>
        </>
      )}

      <section className="card">
        <div className="card-head"><h2>Data quality</h2><span className="muted">{q.usable_reviews} of {q.total_rows} rows usable</span></div>
        <div className="quality">
          {["empty_review", "duplicate_review", "missing_rating", "invalid_rating", "invalid_date", "emoji_only", "html_cleaned", "possible_prompt_injection"].map((k) => (
            <div key={k}><span>{ISSUE_LABELS[k]}</span><b>{q[k]}</b></div>
          ))}
        </div>
      </section>
    </>
  );
}
