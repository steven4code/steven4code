"""JarvisHealth — Einstiegspunkt für die Ein-Datei-App (PyInstaller).

Doppelklick-Erlebnis: startet den Server, wartet bis er antwortet und
öffnet dann den Browser. Alle Nutzerdaten (.env, SQLite) liegen in einem
festen Ordner im Benutzerprofil — die App selbst kann irgendwo liegen
(Downloads, Desktop, USB-Stick) und bleibt read-only.
"""
from __future__ import annotations

import multiprocessing
import os
import shutil
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path


def resource_dir() -> Path:
    """Gebündelte Ressourcen (frontend_dist, .env.example) im Frozen-Modus."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """Plattform-üblicher Ort für Nutzerdaten."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    d = base / "JarvisHealth"
    (d / "data").mkdir(parents=True, exist_ok=True)
    return d


def pick_port(start: int = 8000, tries: int = 10) -> int:
    for p in range(start, start + tries):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start


def open_when_ready(url: str) -> None:
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{url}/health", timeout=1)
            break
        except Exception:  # noqa: BLE001 — Server bootet noch
            time.sleep(0.5)
    webbrowser.open(url)


def main() -> None:
    d = data_dir()

    # .env beim ersten Start aus der gebündelten Vorlage anlegen (Demo-Modus).
    env_file = d / ".env"
    if not env_file.exists():
        template = resource_dir() / ".env.example"
        if template.exists():
            shutil.copy(template, env_file)

    # CWD = Datenordner: pydantic-settings findet die .env, und die relative
    # SQLite-URL (./data/health.db) landet ebenfalls hier.
    os.chdir(d)

    from app.main import app  # Import erst NACH chdir (Settings lesen .env)
    import uvicorn

    port = pick_port(8000)
    url = f"http://localhost:{port}"

    print()
    print("  JarvisHealth — dein Tagesbriefing")
    print(f"  → {url}  (der Browser öffnet sich gleich automatisch)")
    print(f"  Deine Daten liegen in: {d}")
    print("  Beenden: dieses Fenster schließen oder Strg+C")
    print()

    threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
