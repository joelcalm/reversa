import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import BriefingFocus from "./pages/BriefingFocus";
import BriefingRoom from "./pages/BriefingRoom";
import DataQuality from "./pages/DataQuality";
import GraphExplorer from "./pages/GraphExplorer";

const NAV = [
  { to: "/", label: "Briefing Room", end: true },
  { to: "/explorer", label: "Explorer" },
  { to: "/data-quality", label: "Data Quality" },
];

function LegacyHashRedirect({ hash }: { hash: string }) {
  return <Navigate to={{ pathname: "/", hash }} replace />;
}

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="container topbar-inner">
          <NavLink to="/" className="brand">
            <span className="brand-mark" />
            BOE Knowledge Graph
          </NavLink>
          <nav className="nav">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} end={n.end} className={({ isActive }) => (isActive ? "active" : "")}>
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main>
        <div className="container">
          <Routes>
            <Route path="/" element={<BriefingRoom />} />
            <Route path="/briefing/:slug" element={<BriefingFocus />} />
            <Route path="/explorer" element={<GraphExplorer />} />
            <Route path="/data-quality" element={<DataQuality />} />
            <Route path="/council" element={<Navigate to="/" replace />} />
            <Route path="/briefings/unreadable" element={<Navigate to="/briefing/unreadable-laws" replace />} />
            <Route path="/briefings/omnibus" element={<LegacyHashRedirect hash="#briefing-omnibus" />} />
            <Route path="/briefings/dead-law" element={<Navigate to="/briefing/dead-law" replace />} />
            <Route path="/briefings/ley-30-1992" element={<Navigate to="/briefing/ley-30-1992" replace />} />
          </Routes>
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          BOE Knowledge Graph — consolidated legislation as a graph of amendments, repeals and
          citations. Data source:{" "}
          <a href="https://boe.es/datosabiertos/" target="_blank" rel="noreferrer">
            BOE open data
          </a>
          .
        </div>
      </footer>
    </div>
  );
}
