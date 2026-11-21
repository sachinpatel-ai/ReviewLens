import { AlertTriangle, Inbox } from "lucide-react";

export function Loading({ label = "Loading…" }) {
  return (
    <div className="state" role="status">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  );
}

export function EmptyState({ icon: Icon = Inbox, title, text, action }) {
  return (
    <div className="state">
      <div className="icon"><Icon size={22} /></div>
      <h2>{title}</h2>
      {text && <p>{text}</p>}
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state error" role="alert">
      <div className="icon"><AlertTriangle size={22} /></div>
      <h2>Something went wrong</h2>
      <p>{message}</p>
      {onRetry && <button className="btn" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function KpiCard({ icon: Icon, label, value, hint, tone = "acc" }) {
  return (
    <div className={`card kpi ${tone}`}>
      <div className="label"><Icon size={14} /> {label}</div>
      <div className="value">{value}</div>
      {hint && <div className="hint">{hint}</div>}
    </div>
  );
}

export function SentimentBadge({ sentiment }) {
  return sentiment ? <span className={`badge ${sentiment}`}>{sentiment}</span> : <span className="badge plain">–</span>;
}
