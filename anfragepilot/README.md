# AnfragePilot Handwerk – MVP

Anfrage- und Angebots-Vorsystem für Handwerksbetriebe (Pilotvertikale: **SHK**),
umgesetzt nach dem Masterdokument *„AnfragePilot Handwerk – Masterdokument für
KI-Übergabe, Kunden-Pitch und MVP-Build“*.

Die Kernkette bleibt in jedem Fall erhalten:

> **Anfrage erfassen → analysieren → fehlende Angaben erkennen → Rückfrage
> vorbereiten → internes Angebots-Briefing erstellen → Dashboard/Freigabe-Queue
> aktualisieren → Mensch prüft und gibt frei.**

Es wird **nichts automatisch an Kunden versendet** – jeder Rückfrageentwurf
braucht eine manuelle Freigabe (Human-in-the-loop). Nach der Freigabe öffnet
ein Klick den Entwurf im eigenen Mailprogramm.

## Schnellstart

```bash
cd anfragepilot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 15 synthetische Demo-Fälle laden (regelbasiert, ohne API-Key)
python seed_demo.py

# Dashboard starten
uvicorn app.main:app --reload
# -> http://localhost:8000
```

Tests:

```bash
pytest
```

## KI-Analyse (Claude) vs. regelbasierter Fallback

| Modus | Wann aktiv | Verhalten |
|---|---|---|
| **Claude** (`claude-opus-4-8`) | `ANTHROPIC_API_KEY` gesetzt (oder `ANFRAGEPILOT_USE_LLM=on`) | Klassifikation, Extraktion, Missing-Fields, Rückfrageentwurf und Briefing per Messages API mit strukturiertem JSON-Output (`output_config.format`, Schema-erzwungen) |
| **Regelbasiert** | kein Key / `off` / LLM-Fehler | Deterministische Keyword-/Regex-Analyse mit identischer Ergebnisstruktur |

Fällt der LLM-Aufruf aus (Netz, Refusal, Quota), greift automatisch der
regelbasierte Fallback – der Anfrageeingang blockiert nie. Jeder Analyse-Lauf
wird mit Modell, Prompt-Version und Roh-Output in `ai_outputs` protokolliert;
Fallback-Fälle erscheinen im Monatsreport als „KI-Fehlerfälle“.

Konfiguration über Umgebungsvariablen (siehe `.env.example`).

## Umgesetzte MVP-Muss-Funktionen (Masterdokument 7.1 / 20.2)

| # | Anforderung | Umsetzung |
|---|---|---|
| 1 | E-Mail-/Formular-Eingang erfassen | `POST /api/anfragen` (Webhook für n8n/Make/Formular) + Erfassungsmaske `/neu`; Kanal `email`/`formular`; Dublettenmarkierung |
| 2 | Anfrage automatisch zusammenfassen | KI-Zusammenfassung je Fall (LLM oder Regeln) |
| 3 | Kundendaten extrahieren | Name, E-Mail, Telefon, Objektadresse, Ort |
| 4 | Gewerk & Anfrageart erkennen | SHK; 3 Anfragearten: Heizungstausch, Badsanierung, Reparatur/Notdienst |
| 5 | Dringlichkeit erkennen | Priorität A/B/C mit Begründung (Notdienst/B2B → A, außerhalb Einzugsgebiet/unklar → C) |
| 6 | Fehlende Informationen erkennen | Pflichtfeldlisten je Anfrageart (aus Abschnitt 8), Abgleich vorhanden/fehlend/unsicher |
| 7 | Rückfrage-E-Mail vorbereiten | Entwurf nach Regeln aus 10.3 (≤ ~140 Wörter, keine Preis-/Terminzusagen, `[Betrieb]`-Signatur) |
| 8 | Internes Angebots-Briefing | Vollständiges Briefing inkl. interner Checkliste je Anfrageart |
| 9 | Priorität vergeben | A/B/C, Sortierung im Dashboard |
| 10 | Status erfassen | 8 Statuswerte aus Modul 6 |
| 11 | Fallübersicht | SQLite + serverseitiges Dashboard mit Filtern (Status/Prio/Freigabe) |
| 12 | Manuelle Freigabe | Freigabe-Queue: Entwurf bearbeiten, freigeben, ablehnen; erst danach Mailto-Versand |
| 13 | Monatsreporting | `/report`: Volumen, Anteil unvollständig, Top-fehlende Angaben, A/B/C, Ø Zeit bis Freigabe, geschätzte Zeitersparnis |

Zusätzlich (Abschnitt 20.2): AI-Output-Logging, Audit-Log je Fall,
manuelle Statusänderung, Verantwortlichen-Zuordnung.

## Akzeptanzkriterien (20.3)

- Neue Anfragefälle werden zuverlässig angelegt → `tests/test_api.py`
- Fehlende Informationen überwiegend korrekt erkannt → `tests/test_rules.py`
  (u. a. das Becker-Beispiel aus Abschnitt 11.3 mit den dort erwarteten Feldern)
- Rückfrageentwürfe halluzinieren nicht → regelbasiert nur aus Pflichtfeld-Katalog;
  LLM-Prompt verbietet Preise/Termine/Erfundenes, Schema erzwingt Struktur
- Entwürfe manuell prüfbar → Freigabe-Queue mit Bearbeiten/Freigeben/Ablehnen
- Status & Priorität sichtbar → Dashboard + Falldetail
- **≥ 15 Testfälle stabil** → `seed_demo.py` (15 Fälle) + `test_15_demo_faelle_laufen_stabil`

## Bewusst NICHT gebaut (Abschnitte 7.4 / 20.4)

Keine automatische Angebotserstellung, keine Preisberechnung, kein autonomer
Kundenkontakt, kein Voice-Agent, keine Mobile App, kein Multi-Tenant-SaaS,
keine ERP-/DATEV-/GAEB-Integration, keine OCR-/PDF-Analyse (Anhänge werden im
MVP nur referenziert). Diese Ausschlüsse sind im Masterdokument explizit
begründet (Haftung, Komplexität, Datenschutz).

## Architektur

```
E-Mail / Formular / Webhook (n8n, Make, Tally …)
        │  POST /api/anfragen  bzw.  /neu
        ▼
service.eingang_verarbeiten()          ← Fall anlegen, Dublettencheck
        │
        ▼
Analyse: llm.analyse() ──Fehler──► rules.analyse()   (identische Struktur)
        │        Claude Messages API, output_config.format (JSON-Schema)
        ▼
SQLite (inquiries, ai_outputs, audit_log)
        │
        ▼
Dashboard / Freigabe-Queue / Falldetail / Monatsreport (FastAPI + Jinja2)
        │
        ▼
Mensch prüft → gibt frei → Mailto-Link öffnet den Entwurf im Mailprogramm
```

### Datenmodell (nach Abschnitt 9.5)

- `inquiries` – Anfragefall mit allen Dashboard-Feldern aus Modul 7
- `ai_outputs` – Log jedes Analyse-Laufs (Modell, Prompt-Version, Roh-Output, Fehler)
- `audit_log` – jede Aktion (Anlage, Analyse, Entwurf, Freigabe, Statuswechsel) mit Akteur
- Branchen-Templates (Pflichtfelder, Prioritätsregeln, Checklisten) liegen als
  Code-Konfiguration in `app/branchen.py` – pro Pilotkunde anpassbar

## DSGVO-Hinweise für den Pilotbetrieb (Abschnitt 16)

- Datenminimierung: nur Betreff/Nachricht/Kontaktdaten werden an das LLM übergeben,
  Anhänge werden im MVP nicht hochgeladen oder analysiert
- Menschliche Freigabe ist technisch erzwungen (kein automatischer Versand)
- Vor Produktivbetrieb: AVV mit Anthropic prüfen, Löschkonzept definieren
  (SQLite-Datei liegt lokal unter `data/`), Rollen-/Rechtekonzept ergänzen
