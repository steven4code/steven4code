# JarvisHealth

Ein lokales, modernes Dark-Mode-Dashboard für deine Fitbit-/Google-Health-Daten
mit **wissenschaftlich fundierten** Eigenberechnungen.

**Oberfläche:** aufgeräumter, einspaltiger Feed im Bevel-Stil – eine Metrik pro
Karte (großer Wert + Sparkline + 1 Satz Klartext), Tap öffnet die Detailansicht.
Zusätzliche Karten: VO₂max, Ruhepuls, HFV, Schritte, aktive Energie, Active Zone
Minutes. Der **Strain** nutzt echte **Ganztags-/Intraday-HF** (Minuten-Puls für
heute, Tages-Zonen-Rollups für die Historie).

Kernmetriken:

- **Erholung** – lnRMSSD vs. 60-Tage-Baseline ±SWC + 7-Tage-Trend/CV, gewichtet
  mit Schlaf-HF und Schlaf; Temp/Atmung/SpO₂ als Anomalie-Flags.
- **Tages-Belastung (Strain 0–21)** – logarithmische kardiovaskuläre Last über
  den Tag, mit Ziel-Range (aus Erholung+Schlaf+chronischer Last) und Rest-Budget
  inkl. konkreter Zonen-Optionen ("noch ~X′ Z2 oder ~Y′ Z4").
- **Schlaf** – Sleep Regularity Index (SRI) als Top-Komponente + Dauer/Effizienz/
  Tief/REM/Latenz/WASO; automatischer Schlafbedarf + Defizit.
- **Cardio Load** – schwellen-basierte HF-Zonen (LTHR), Edwards-Zonen-TRIMP +
  sRPE, EWMA-Last/Monotonie, polarisierte Zielverteilung und erholungs-validierte
  Trainingsempfehlungen für dein 5–10 km-Ziel (inkl. Padel).

Jede Karte ist anklickbar → Detailansicht. Backend: FastAPI + SQLite. Frontend:
React + Vite + Recharts. Läuft komplett lokal.

![Dashboard](docs/dashboard.png)
![Strain-Detail](docs/strain.png)

---

## 1. Lokal testen (sofort, ohne Konto)

Standardmäßig läuft alles mit einem **Demo-Provider** (realistische Beispieldaten,
deterministisch). Kein Google-Konto nötig.

```bash
# Backend (Terminal 1)
cd backend
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # USE_MOCK_PROVIDER=true
uvicorn app.main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

→ **http://localhost:5173** öffnen. Die App synchronisiert beim Start automatisch.
Unter ⚙ kannst du Max-HF (194), LTHR, Trainingsziel und Schlafbedarf einstellen.

---

## 2. Echte Daten anbinden (Google Health API)

Die alte Fitbit Web API wird **9/2026** abgeschaltet; Nachfolger ist die
**Google Health API** (`https://health.googleapis.com/v4/…`, Google OAuth 2.0).
Login-Flow, Token-Speicherung, Auto-Refresh und der REST-Client sind bereits
implementiert – es fehlen nur **deine** Zugangsdaten.

### Schritt 1 – Google Cloud (einmalig, nur du kannst das)
1. Projekt in der [Google Cloud Console](https://console.cloud.google.com/) anlegen.
2. **Google Health API** aktivieren (APIs & Services → Library).
3. **OAuth consent screen**: User type *External*, Status **Testing**, dich als
   **Test user** eintragen. Read-only Health-Scopes hinzufügen.
4. **Credentials → OAuth client ID → Web application**, Redirect-URI
   `http://localhost:8000/auth/callback`. **Client ID + Secret** notieren.

### Schritt 2 – `.env` setzen
```ini
USE_MOCK_PROVIDER=false
GOOGLE_CLIENT_ID=…
GOOGLE_CLIENT_SECRET=…
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
HEALTH_SCOPES=https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly https://www.googleapis.com/auth/googlehealth.sleep.readonly https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly
```

### Schritt 3 – Anmelden
Backend & Frontend neu starten → im Login-Gate „Mit Google anmelden" → Google-
Consent → zurück zur App → **Sync**.

### ⚠ Vor dem Live-Gang zu prüfen
Die offiziellen Doku-Seiten waren aus der Build-Umgebung nicht abrufbar (Google
liefert 403 an automatisierte Abrufe). Die API-**Struktur** ist korrekt
umgesetzt; bitte die **exakten Werte** gegen die Doku abgleichen — alles an
**einer** Stelle:
- **Scopes**: `developers.google.com/health/scopes` → ggf. `HEALTH_SCOPES` anpassen.
- **Datentyp-Namen** (kebab-case): `developers.google.com/health/data-types` →
  `backend/app/providers/google_health.py` → `DATA_TYPES`.
- **Endpoint/Methode**: `…/v4/users/me/dataTypes/{type}/dataPoints` (list /
  dailyRollUp) ist in `google_health.py` zentralisiert.

Hinweis: Im OAuth-**Testing**-Modus laufen Refresh-Tokens nach 7 Tagen ab
(wöchentlich neu anmelden) – für Dauerbetrieb App auf **Produktion** stellen.

---

## Berechnungslogik (Kurzreferenz)

| Metrik | Kern | Quelle/Standard |
| --- | --- | --- |
| Erholung | lnRMSSD vs 60-T-Baseline ±SWC, 7-T-Trend/CV; Mix HFV 50 / HF 20 / Schlaf 30; Temp/Atmung/SpO₂-Flags | Plews/Buchheit; WHOOP/Oura |
| Strain 0–21 | log. kardiovask. Last; Ziel-Range aus Erholung+Schlaf+ACWR; Rest-Budget → Zonen | WHOOP Strain/Strain-Coach |
| Schlaf | SRI (30%) + Dauer/Effizienz/Tief/REM/Latenz/WASO; Auto-Bedarf + Debt | Oura; SRI-Mortalitätsstudien |
| Cardio | LTHR-Zonen; Edwards-TRIMP + sRPE; EWMA/Monotonie; polarisiert 80/20 | Seiler; Foster; HFV-gesteuert |

Details inkl. Formeln stehen als Kommentare in `backend/app/services/`
(`recovery.py`, `strain.py`, `sleep.py`, `cardio.py`, `profile.py`).

## Projektstruktur
```
backend/app/
  providers/   mock.py · google_health.py (DATA_TYPES/Scopes hier anpassen)
  services/    recovery · strain · sleep · cardio · profile · dashboard · sync
  routers/     auth · sync · metrics (+ /detail/*) · profile
frontend/src/
  App.jsx      Layout + Navigation (JarvisHealth)
  components/   RecoveryHero · StrainPanel · SleepCard · CardioCard · *Detail · Settings · StrainGauge
```

## Datenschutz
Nur Lesen (`*.readonly`, GET). Alle Scores werden **lokal** berechnet, nichts
wird zu Google zurückgeschrieben. Daten/Tokens bleiben in deiner lokalen SQLite.
