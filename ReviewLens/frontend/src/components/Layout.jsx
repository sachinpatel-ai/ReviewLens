import { FileUp, LayoutDashboard, ListChecks, Search } from "lucide-react";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "reviews", label: "Reviews", icon: ListChecks },
  { id: "upload", label: "Upload CSV", icon: FileUp },
];

export default function Layout({ page, onNavigate, title, subtitle, actions, children }) {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Search size={16} color="#fff" /></div>
          <span className="name">ReviewLens</span>
        </div>
        <nav className="nav" aria-label="Main">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button key={id} className={page === id ? "active" : ""} onClick={() => onNavigate(id)} aria-current={page === id ? "page" : undefined}>
              <Icon size={17} /> {label}
            </button>
          ))}
        </nav>
        <p className="side-note">Reviews are analyzed by Gemini. Review text is treated as data, never as instructions.</p>
      </aside>
      <div className="main">
        <header className="header">
          <div>
            <h1>{title}</h1>
            {subtitle && <p className="header-sub">{subtitle}</p>}
          </div>
          <div className="toolbar">{actions}</div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
