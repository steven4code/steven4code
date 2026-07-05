#!/bin/bash
# JarvisHealth — Doppelklick-Start für macOS (und Linux).
# Erster Start richtet alles automatisch ein (dauert ein paar Minuten),
# danach startet die App in Sekunden und öffnet den Browser.
#
# macOS-Hinweis: Beim allerersten Öffnen ggf. Rechtsklick -> "Öffnen"
# (Gatekeeper-Warnung bei heruntergeladenen Skripten).
set -e
cd "$(dirname "$0")"

URL="http://localhost:8000"

say() { printf "\n\033[1;36m▸ %s\033[0m\n" "$1"; }
fail() { printf "\n\033[1;31m✗ %s\033[0m\n" "$1"; read -r -p "Enter zum Schließen …"; exit 1; }

open_browser() {
  if command -v open >/dev/null; then open "$URL"; elif command -v xdg-open >/dev/null; then xdg-open "$URL"; fi
}

# --------------------------------------------------------------------------
# Weg 1: Python 3.10+ und Node vorhanden -> nativer Ein-Prozess-Start
# --------------------------------------------------------------------------
if command -v python3 >/dev/null && command -v npm >/dev/null; then
  [ -f backend/.env ] || { say "Erstelle backend/.env (Demo-Modus)"; cp backend/.env.example backend/.env; }

  if [ ! -d backend/.venv ]; then
    say "Erste Einrichtung: Python-Umgebung (einmalig)"
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install -q -r backend/requirements.txt
  fi

  if [ ! -d frontend/dist ] || [ frontend/src -nt frontend/dist ]; then
    say "Baue die Oberfläche (einmalig bzw. nach Updates)"
    (cd frontend && npm install --silent && npm run build --silent)
  fi

  say "Starte JarvisHealth auf $URL"
  (sleep 2 && open_browser) &
  cd backend && exec .venv/bin/uvicorn app.main:app --port 8000

# --------------------------------------------------------------------------
# Weg 2: Docker Desktop vorhanden
# --------------------------------------------------------------------------
elif command -v docker >/dev/null; then
  [ -f backend/.env ] || cp backend/.env.example backend/.env
  say "Starte über Docker (erster Start baut die Container, dauert etwas)"
  (sleep 8 && URL="http://localhost:5173" open_browser) &
  exec docker compose up --build

# --------------------------------------------------------------------------
# Nichts gefunden -> freundliche Anleitung
# --------------------------------------------------------------------------
else
  fail "Bitte einmalig installieren: Python 3 (python.org) UND Node.js (nodejs.org) — oder Docker Desktop (docker.com). Danach dieses Skript erneut doppelklicken."
fi
