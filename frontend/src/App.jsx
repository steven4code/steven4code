import { useCallback, useEffect, useState } from "react";
import { getAuthStatus, getDashboard, runSync } from "./api.js";
import RecoveryHero from "./components/RecoveryHero.jsx";
import SleepCard from "./components/SleepCard.jsx";
import StrainCard from "./components/StrainCard.jsx";
import CardioCard from "./components/CardioCard.jsx";
import Vo2Card from "./components/Vo2Card.jsx";
import RecoveryDetail from "./components/RecoveryDetail.jsx";
import StrainDetail from "./components/StrainDetail.jsx";
import SleepDetail from "./components/SleepDetail.jsx";
import CardioDetail from "./components/CardioDetail.jsx";
import MetricDetail from "./components/MetricDetail.jsx";
import Settings from "./components/Settings.jsx";
import LoginScreen from "./components/LoginScreen.jsx";

const RANGES = [7, 14, 30, 90];
const RANGE_LABEL = { 7: "Woche", 14: "14T", 30: "30T", 90: "90T" };

export default function App() {
  const [auth, setAuth] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [days, setDays] = useState(30);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState({ name: "dashboard" });

  const loadDashboard = useCallback(async (d) => setDashboard(await getDashboard(d)), []);
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
  const vo2 = (d?.extras || []).find((e) => e.key === "vo2max");

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1 className="brand">Jarvis<span>Health</span></h1>
          <p className="sub">
            {auth?.mock_mode ? <span className="badge mock">Demo-Daten</span>
              : auth?.authenticated ? <span className="badge live">Google Health</span>
              : <span className="badge off">Offline</span>}
            {d?.as_of && <> · Stand {d.as_of}</>}
          </p>
        </div>
        <div className="controls">
          <div className="range">
            {RANGES.map((r) => (
              <button key={r} className={r === days ? "active" : ""} onClick={() => setDays(r)}>{RANGE_LABEL[r]}</button>
            ))}
          </div>
          <button className="btn" onClick={() => setView({ name: "settings" })} title="Einstellungen">⚙</button>
          <button className="btn primary" onClick={onSyncClick} disabled={syncing}>{syncing ? "…" : "Sync"}</button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}
      {!dashboard && !error && <div className="loading">Lade Dashboard…</div>}
      {dashboard?.empty && <div className="notice">Noch keine Daten. Klicke auf „Sync".</div>}

      {d && (
        <main>
          <RecoveryHero card={d.recovery} onOpen={() => setView({ name: "recovery" })} />

          <div className="grid2">
            <SleepCard card={d.sleep} onOpen={() => setView({ name: "sleep" })} />
            <StrainCard card={d.strain} onOpen={() => setView({ name: "strain" })} />
          </div>

          <CardioCard card={d.cardio} onOpen={() => setView({ name: "cardio" })} />

          {vo2 && <Vo2Card extra={vo2} onOpen={() => setView({ name: "metric", extra: vo2 })} />}
        </main>
      )}
    </div>
  );
}
