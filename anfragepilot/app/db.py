"""SQLite-Datenschicht: Anfragefälle, AI-Output-Log, Audit-Log."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "anfragepilot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fall_id TEXT UNIQUE NOT NULL,
    kanal TEXT NOT NULL,
    eingang_ts TEXT NOT NULL,
    absender_name TEXT DEFAULT '',
    absender_email TEXT DEFAULT '',
    telefon TEXT DEFAULT '',
    betreff TEXT DEFAULT '',
    rohtext TEXT DEFAULT '',
    anhaenge TEXT DEFAULT '[]',
    objektadresse TEXT DEFAULT '',
    ort TEXT DEFAULT '',
    gewerk TEXT DEFAULT '',
    anfrageart TEXT DEFAULT '',
    zusammenfassung TEXT DEFAULT '',
    vorhandene_angaben TEXT DEFAULT '[]',
    fehlende_angaben TEXT DEFAULT '[]',
    unsichere_angaben TEXT DEFAULT '[]',
    unsicherheiten TEXT DEFAULT '[]',
    prioritaet TEXT DEFAULT '',
    status TEXT DEFAULT 'Neu',
    rueckfrage_entwurf TEXT DEFAULT '',
    internes_briefing TEXT DEFAULT '',
    naechster_schritt TEXT DEFAULT '',
    freigabe_status TEXT DEFAULT 'offen',
    verantwortlicher TEXT DEFAULT '',
    letzte_aktion TEXT DEFAULT '',
    duplikat_von TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_outputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inquiry_id INTEGER NOT NULL REFERENCES inquiries(id),
    output_type TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT DEFAULT '',
    raw_output TEXT DEFAULT '',
    error TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inquiry_id INTEGER NOT NULL REFERENCES inquiries(id),
    action_type TEXT NOT NULL,
    actor TEXT DEFAULT 'system',
    old_value TEXT DEFAULT '',
    new_value TEXT DEFAULT '',
    comment TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def db_path() -> Path:
    return Path(os.environ.get("ANFRAGEPILOT_DB", str(DEFAULT_DB)))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
