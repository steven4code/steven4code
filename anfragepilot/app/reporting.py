"""Monatsreporting (Modul 8): macht den Nutzen des Systems messbar."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from . import db

# Konservative Annahme aus der ROI-Rechnung (Abschnitt 14.2):
# 25 min manuelle Vorqualifikation pro Anfrage, 30 % Ersparnis => 7,5 min/Anfrage.
ERSPARNIS_MIN_PRO_ANFRAGE = 7.5


def verfuegbare_monate() -> list[str]:
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(created_at, 1, 7) AS monat FROM inquiries ORDER BY monat DESC"
        ).fetchall()
        return [r["monat"] for r in rows]


def monatsreport(monat: str = "") -> dict:
    """monat im Format 'YYYY-MM'; leer = aktueller Monat."""
    if not monat:
        monat = datetime.utcnow().strftime("%Y-%m")
    with db.get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM inquiries WHERE substr(created_at, 1, 7) = ?", (monat,)
        ).fetchall()
        faelle = [dict(r) for r in rows]
        ids = [f["id"] for f in faelle]

        fehlende_counter: Counter = Counter()
        unvollstaendig = 0
        entwuerfe = 0
        for f in faelle:
            fehlend = json.loads(f["fehlende_angaben"] or "[]")
            if fehlend:
                unvollstaendig += 1
                fehlende_counter.update(fehlend)
            if f["rueckfrage_entwurf"]:
                entwuerfe += 1

        prio = Counter(f["prioritaet"] for f in faelle if f["prioritaet"])
        status = Counter(f["status"] for f in faelle)
        kanaele = Counter(f["kanal"] for f in faelle)

        freigegeben = sum(1 for f in faelle if f["freigabe_status"] == "freigegeben")
        abgelehnt = sum(1 for f in faelle if f["freigabe_status"] == "abgelehnt")

        # Zeit bis zur ersten Freigabe als Näherung für "Zeit bis erste Aktion".
        minuten: list[float] = []
        if ids:
            platzhalter = ",".join("?" for _ in ids)
            audit_rows = conn.execute(
                f"SELECT inquiry_id, MIN(created_at) AS ts FROM audit_log"
                f" WHERE action_type = 'entwurf_freigegeben' AND inquiry_id IN ({platzhalter})"
                f" GROUP BY inquiry_id",
                ids,
            ).fetchall()
            erstellt = {f["id"]: f["created_at"] for f in faelle}
            for row in audit_rows:
                try:
                    start = datetime.fromisoformat(erstellt[row["inquiry_id"]])
                    ende = datetime.fromisoformat(row["ts"])
                    minuten.append((ende - start).total_seconds() / 60)
                except (ValueError, KeyError):
                    continue

        fehler = conn.execute(
            "SELECT COUNT(*) FROM ai_outputs WHERE error != ''"
            " AND substr(created_at, 1, 7) = ?", (monat,)
        ).fetchone()[0]

        anzahl = len(faelle)
        return {
            "monat": monat,
            "anzahl_eingegangen": anzahl,
            "anzahl_strukturiert": sum(1 for f in faelle if f["zusammenfassung"]),
            "anzahl_entwuerfe": entwuerfe,
            "anzahl_freigegeben": freigegeben,
            "anzahl_abgelehnt": abgelehnt,
            "anteil_unvollstaendig": round(unvollstaendig / anzahl * 100) if anzahl else 0,
            "top_fehlende": fehlende_counter.most_common(5),
            "prioritaeten": {p: prio.get(p, 0) for p in ("A", "B", "C")},
            "status_verteilung": dict(status),
            "kanaele": dict(kanaele),
            "avg_minuten_bis_freigabe": round(sum(minuten) / len(minuten), 1) if minuten else None,
            "ki_fehlerfaelle": fehler,
            "ersparnis_minuten": round(anzahl * ERSPARNIS_MIN_PRO_ANFRAGE),
        }
