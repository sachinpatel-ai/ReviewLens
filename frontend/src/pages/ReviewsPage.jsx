import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, ListChecks, TriangleAlert } from "lucide-react";
import ReviewDrawer from "../components/ReviewDrawer";
import { EmptyState, ErrorState, Loading, SentimentBadge } from "../components/ui";
import { errorMessage, getReviews } from "../services/api";
import { fmtDate, STATUS_LABELS } from "../utils/format";

const PAGE_SIZE = 15;
const INITIAL = { search: "", sentiment: "", rating: "", category: "", status: "", sort: "id", order: "asc" };

export default function ReviewsPage({ batchId, categories }) {
  const [filters, setFilters] = useState(INITIAL);
  const [debounced, setDebounced] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [tick, setTick] = useState(0);

  useEffect(() => { const t = setTimeout(() => setDebounced(filters.search), 300); return () => clearTimeout(t); }, [filters.search]);
  useEffect(() => { setPage(1); }, [debounced, filters.sentiment, filters.rating, filters.category, filters.status, filters.sort, filters.order, batchId]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const params = { batch_id: batchId ?? undefined, page, page_size: PAGE_SIZE, sort: filters.sort, order: filters.order };
    if (debounced) params.search = debounced;
    ["sentiment", "rating", "category", "status"].forEach((k) => filters[k] && (params[k] = filters[k]));
    getReviews(params)
      .then((d) => !cancelled && (setData(d), setError(null)))
      .catch((e) => !cancelled && setError(errorMessage(e)))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
    // eslint-disable-next-line
  }, [batchId, page, debounced, filters.sentiment, filters.rating, filters.category, filters.status, filters.sort, filters.order, tick]);

  const set = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }));
  const pages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const filtered = Object.entries(filters).some(([k, v]) => v && !["sort", "order"].includes(k));

  return (
    <>
      <div className="card">
        <div className="toolbar">
          <input type="search" placeholder="Search reviews, summaries, products…" value={filters.search} onChange={set("search")} aria-label="Search reviews" />
          <select value={filters.sentiment} onChange={set("sentiment")} aria-label="Sentiment"><option value="">All sentiments</option><option>Positive</option><option>Neutral</option><option>Negative</option></select>
          <select value={filters.rating} onChange={set("rating")} aria-label="Rating"><option value="">All ratings</option>{[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{n} stars</option>)}</select>
          <select value={filters.category} onChange={set("category")} aria-label="Category"><option value="">All categories</option>{categories.map((c) => <option key={c}>{c}</option>)}</select>
          <select value={filters.status} onChange={set("status")} aria-label="Status"><option value="">All statuses</option>{Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
          <select value={`${filters.sort}:${filters.order}`} onChange={(e) => { const [sort, order] = e.target.value.split(":"); setFilters((f) => ({ ...f, sort, order })); }} aria-label="Sort">
            <option value="id:asc">Original order</option><option value="date:desc">Newest first</option><option value="date:asc">Oldest first</option>
            <option value="rating:desc">Rating: high to low</option><option value="rating:asc">Rating: low to high</option>
            <option value="sentiment_score:desc">Most positive</option><option value="sentiment_score:asc">Most negative</option>
          </select>
          {filtered && <button className="btn" onClick={() => setFilters(INITIAL)}>Clear filters</button>}
        </div>
      </div>

      <div className="card">
        {loading && !data ? <Loading label="Loading reviews…" />
          : error ? <ErrorState message={error} onRetry={() => setTick((t) => t + 1)} />
          : !data || data.total === 0 ? (
            <EmptyState icon={ListChecks} title={filtered ? "No reviews match these filters" : "No reviews yet"}
              text={filtered ? "Try removing a filter or searching for something else." : "Upload a CSV to see reviews here."} />
          ) : (
            <>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Product</th><th>Review</th><th>Rating</th><th>Sentiment</th><th>Category</th><th>Date</th></tr></thead>
                  <tbody>
                    {data.items.map((r) => (
                      <tr key={r.id} onClick={() => setSelected(r)} tabIndex={0} onKeyDown={(e) => e.key === "Enter" && setSelected(r)}>
                        <td>{r.product}</td>
                        <td className="text"><div>{r.clean_text || <span className="muted">(empty review)</span>}</div>
                          {r.status !== "analyzed" && <span className="badge plain" style={{ marginTop: 4 }}>{STATUS_LABELS[r.status]}</span>}</td>
                        <td>{r.rating ? `${r.rating}★` : <span className="muted">–</span>}{r.rating_mismatch && <TriangleAlert size={14} color="#b58a1b" style={{ marginLeft: 6, verticalAlign: "text-bottom" }} aria-label="Rating and text disagree" />}</td>
                        <td><SentimentBadge sentiment={r.sentiment} /></td>
                        <td>{r.category || <span className="muted">–</span>}</td>
                        <td>{fmtDate(r.review_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="pager">
                <span className="muted">{data.total} reviews · page {page} of {pages}</span>
                <span className="toolbar">
                  <button className="btn" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}><ChevronLeft size={16} /> Previous</button>
                  <button className="btn" disabled={page >= pages} onClick={() => setPage((p) => p + 1)}>Next <ChevronRight size={16} /></button>
                </span>
              </div>
            </>
          )}
      </div>
      {selected && <ReviewDrawer review={selected} onClose={() => setSelected(null)} />}
    </>
  );
}
