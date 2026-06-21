import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import UnreadableLaws from "./pages/UnreadableLaws";
import OmnibusLaws from "./pages/OmnibusLaws";
import DeadLawDependencies from "./pages/DeadLawDependencies";
import BlastRadius from "./pages/BlastRadius";
import GraphExplorer from "./pages/GraphExplorer";

const NAV = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/briefings/unreadable", label: "1 · Unreadable" },
  { to: "/briefings/omnibus", label: "2 · Omnibus" },
  { to: "/briefings/dead-law", label: "3 · Dead law" },
  { to: "/briefings/ley-30-1992", label: "4 · Ley 30/1992" },
  { to: "/explorer", label: "Graph explorer" },
];

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
            <Route path="/" element={<Dashboard />} />
            <Route path="/briefings/unreadable" element={<UnreadableLaws />} />
            <Route path="/briefings/omnibus" element={<OmnibusLaws />} />
            <Route path="/briefings/dead-law" element={<DeadLawDependencies />} />
            <Route path="/briefings/ley-30-1992" element={<BlastRadius />} />
            <Route path="/explorer" element={<GraphExplorer />} />
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
