import { useCallback, useEffect, useState } from "react";
import { getAuthStatus, getDashboard, runSync } from "./api.js";
import HeroBrief from "./components/HeroBrief.jsx";
import CoachCard from "./components/CoachCard.jsx";
import SleepCard from "./components/SleepCard.jsx";
import StrainCard from "./components/StrainCard.jsx";
import CardioCard from "./components/CardioCard.jsx";
import TrendGrid from "./components/TrendGrid.jsx";
import RecoveryDetail from "./components/RecoveryDetail.jsx";
import StrainDetail from "./components/StrainDetail.jsx";
import SleepDetail from "./components/SleepDetail.jsx";
import CardioDetail from "./components/CardioDetail.jsx";
import MetricDetail from "./components/MetricDetail.jsx";
import Settings from "./components/Settings.jsx";
import LoginScreen from "./components/LoginScreen.jsx";

// Feed-Reihenfolge = Entscheidungshierarchie (docs/DESIGN.md §2):
// Briefing → Coach → Schlaf → Belastung → Training → Trends.
export default function App() {
  const [auth, setAuth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [days, setDays] = useState(30);
  const [syncing, setSyncing] = useState(false);
  const [refetching, setRefetching] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState({ name: "dashboard" });

  // Refetch dimmt den letzten Render, statt ihn zu ersetzen (kein Skeleton-Flackern).
  const loadDashboard = useCallback(async (d) => {
    setRefetching(true);
    try {
      setDashboard(await getDashboard(d));
    } finally {
      setRefetching(false);
    }
  }, []);
  const doSync = useCallback(async () => {
    setSyncing(true); setError(null);
    try { await runSync(); } catch (e) { setError(e.message); } finally { setSyncing(false); }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const status = await getAuthStatus();
        setAuth(status);
        if (status.mock_mode || status.authenticated) await doSync();
      } catch (e) { setError(e.message); }
      try { await loadDashboard(days); } catch (e) { setError(e.message); }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { loadDashboard(days).catch((e) => setError(e.message)); }, [days, loadDashboard]);

  const onSyncClick = async () => { await doSync(); await loadDashboard(days); };
  const back = () => setView({ name: "dashboard" });

  const needsConnect = auth && !auth.mock_mode && !auth.authenticated;
  if (needsConnect) return <LoginScreen error={error} />;
  if (view.name === "recovery") return <RecoveryDetail onBack={back} />;
  if (view.name === "strain") return <StrainDetail onBack={back} />;
  if (view.name === "sleep") return <SleepDetail onBack={back} />;
  if (view.name === "cardio") return <CardioDetail onBack={back} />;
  if (view.name === "metric") return <MetricDetail extra={view.extra} onBack={back} />;
  if (view.name === "settings")
    return <Settings onBack={back} onSaved={() => loadDashboard(days)} />;

  const d = dashboard && !dashboard.empty ? dashboard : null;

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1 className="brand">Jarvis<span>Health</span></h1>
          <p className="brand-sub">
            {auth?.mock_mode ? <span className="badge mock">Demo-Daten</span>
              : auth?.authenticated ? <span className="badge live">Google Health</span>
              : <span className="badge off">Offline</span>}
          </p>
        </div>
        <div className="controls">
          <div className="range" role="group" aria-label="Zeitraum">
            {[7, 14, 30, 90].map((r) => (
              <button
                key={r}
                type="button"
                className={r === days ? "active" : ""}
                aria-pressed={r === days}
                onClick={() => setDays(r)}
              >
                {r === 7 ? "Woche" : `${r}T`}
              </button>
            ))}
          </div>
          <button type="button" className="btn icon" onClick={() => setView({ name: "settings" })} aria-label="Einstellungen">
            ⚙
          </button>
          <button type="button" className="btn primary" onClick={onSyncClick} disabled={syncing}>
            {syncing ? "Synchronisiert …" : "Sync"}
          </button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}
      {!dashboard && !error && <div className="loading">Lade Tagesbriefing …</div>}
      {dashboard?.empty && <div className="notice">Noch keine Daten. Klicke auf „Sync".</div>}

      {d && (
        <main className={refetching ? "is-refetching" : ""}>
          <HeroBrief
            asOf={d.as_of}
            recovery={d.recovery}
            strain={d.strain}
            sleep={d.sleep}
            onOpen={(name) => setView({ name })}
          />
          <CoachCard strain={d.strain} onOpen={() => setView({ name: "strain" })} />
          <SleepCard card={d.sleep} onOpen={() => setView({ name: "sleep" })} />
          <StrainCard card={d.strain} onOpen={() => setView({ name: "strain" })} />
          <CardioCard card={d.cardio} onOpen={() => setView({ name: "cardio" })} />
          <TrendGrid extras={d.extras} onOpen={(extra) => setView({ name: "metric", extra })} />
        </main>
      )}
    </div>
  );
}
