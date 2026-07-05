@echo off
rem JarvisHealth — Doppelklick-Start fuer Windows.
rem Erster Start richtet alles automatisch ein (dauert ein paar Minuten),
rem danach startet die App in Sekunden und oeffnet den Browser.
setlocal enabledelayedexpansion
cd /d "%~dp0"

set URL=http://localhost:8000

where python >nul 2>nul
if %errorlevel%==0 (
  where npm >nul 2>nul
  if !errorlevel!==0 goto :native
)
where docker >nul 2>nul
if %errorlevel%==0 goto :docker

echo.
echo   Bitte einmalig installieren: Python 3 (python.org) UND Node.js (nodejs.org)
echo   - oder Docker Desktop (docker.com). Danach dieses Skript erneut starten.
echo.
pause
exit /b 1

:native
if not exist backend\.env (
  echo Erstelle backend\.env ^(Demo-Modus^)
  copy backend\.env.example backend\.env >nul
)
if not exist backend\.venv (
  echo Erste Einrichtung: Python-Umgebung ^(einmalig^) ...
  python -m venv backend\.venv
  backend\.venv\Scripts\pip install -q -r backend\requirements.txt
)
if not exist frontend\dist (
  echo Baue die Oberflaeche ^(einmalig^) ...
  pushd frontend
  call npm install --silent
  call npm run build --silent
  popd
)
echo Starte JarvisHealth auf %URL%
start "" %URL%
cd backend
.venv\Scripts\uvicorn app.main:app --port 8000
pause
exit /b 0

:docker
if not exist backend\.env copy backend\.env.example backend\.env >nul
echo Starte ueber Docker ^(erster Start baut die Container^) ...
start "" http://localhost:5173
docker compose up --build
pause
