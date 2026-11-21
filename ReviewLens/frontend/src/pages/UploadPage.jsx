import { useRef, useState } from "react";
import { CheckCircle2, FileUp, Sparkles } from "lucide-react";
import { errorMessage, uploadCsv } from "../services/api";

const MAX_MB = 2;

export default function UploadPage({ onUploaded, onRun, busy }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handle(file) {
    setError(null); setResult(null);
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) return setError("Only .csv files are accepted.");
    if (file.size > MAX_MB * 1024 * 1024) return setError(`File is too large. Maximum size is ${MAX_MB} MB.`);
    setProgress(0);
    try {
      const batch = await uploadCsv(file, setProgress);
      setResult(batch);
      await onUploaded(batch.id);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setProgress(null);
    }
  }

  const c = result?.counts;
  return (
    <>
      <div className="card">
        <div
          className={`drop ${over ? "over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setOver(true); }}
          onDragLeave={() => setOver(false)}
          onDrop={(e) => { e.preventDefault(); setOver(false); handle(e.dataTransfer.files?.[0]); }}
        >
          <FileUp size={28} color="#0e7c86" />
          <h2>Drop a CSV here, or choose a file</h2>
          <p className="muted">Required columns: review_id, product, rating, date, review_text · up to {MAX_MB} MB</p>
          <input ref={input} type="file" accept=".csv,text/csv" hidden onChange={(e) => { handle(e.target.files?.[0]); e.target.value = ""; }} />
          <button className="btn primary" onClick={() => input.current.click()} disabled={progress !== null}>Choose CSV file</button>
          {progress !== null && (
            <div style={{ width: "min(360px, 100%)" }} role="status">
              <div className="progress"><div style={{ width: `${progress}%` }} /></div>
              <p className="muted">{progress < 100 ? `Uploading… ${progress}%` : "Cleaning and saving…"}</p>
            </div>
          )}
        </div>
        {error && <div className="banner error" role="alert" style={{ marginTop: 14 }}><p className="grow">{error}</p></div>}
      </div>

      {result && (
        <div className="card">
          <div className="card-head"><h2><CheckCircle2 size={16} color="#2e7d4f" style={{ verticalAlign: "text-bottom" }} /> Uploaded {result.filename}</h2></div>
          <p style={{ marginBottom: 12 }}>{result.total_rows} rows read. <b>{c.pending}</b> will be analyzed, <b>{c.skipped_empty}</b> skipped as empty, <b>{c.skipped_duplicate}</b> skipped as duplicates. Rows with bad ratings or dates are kept and flagged.</p>
          <button className="btn primary" onClick={() => onRun(result.id)} disabled={busy || c.pending === 0}><Sparkles size={16} /> Run AI analysis</button>
        </div>
      )}
    </>
  );
}
