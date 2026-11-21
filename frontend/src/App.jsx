import { useState } from "react";
import Layout from "./components/Layout";
import DashboardPage from "./pages/DashboardPage";
import ReviewsPage from "./pages/ReviewsPage";
import UploadPage from "./pages/UploadPage";
import useBatches from "./hooks/useBatches";
import { errorMessage, startAnalysis } from "./services/api";

const TITLES = {
  dashboard: ["Dashboard", "Sentiment, themes and recommendations from your reviews"],
  reviews: ["Reviews", "Search, filter and inspect every review"],
  upload: ["Upload", "Add a CSV of product reviews"],
};

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);
  const b = useBatches();

  async function run(id = b.batchId) {
    setBusy(true); setActionError(null);
    try {
      await startAnalysis(id);
      await b.refresh(id);
      setPage("dashboard");
    } catch (e) {
      setActionError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  const selector = b.batches.length > 0 && (
    <select value={b.batchId ?? ""} onChange={(e) => b.select(Number(e.target.value))} aria-label="Choose upload">
      {b.batches.map((x) => <option key={x.id} value={x.id}>#{x.id} · {x.filename}</option>)}
    </select>
  );

  return (
    <Layout page={page} onNavigate={setPage} title={TITLES[page][0]} subtitle={TITLES[page][1]} actions={page !== "upload" && selector}>
      {actionError && <div className="banner error" role="alert"><p className="grow">{actionError}</p></div>}
      {page === "dashboard" && (
        <DashboardPage analytics={b.analytics} current={b.current} loading={b.loading} error={b.error}
          onRetry={() => b.refresh()} onRun={() => run()} busy={busy} onNavigate={setPage} />
      )}
      {page === "reviews" && <ReviewsPage batchId={b.batchId} categories={Object.keys(b.analytics?.category_distribution || {})} key={`${b.batchId}-${b.current?.status}`} />}
      {page === "upload" && <UploadPage onUploaded={(id) => b.refresh(id)} onRun={run} busy={busy} />}
    </Layout>
  );
}
