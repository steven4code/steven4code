"""Fachlogik: Anfrageeingang -> Analyse -> Dashboard-Datensatz -> Freigabe.

Die Kernkette aus dem Masterdokument (Abschnitt 0):
erfassen -> analysieren -> fehlende Angaben erkennen -> Rückfrage vorbereiten
-> internes Briefing -> Freigabe-Queue -> Mensch prüft und gibt frei.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from . import branchen, db, llm, rules


class Eingabefehler(ValueError):
    pass


def _neue_fall_id(conn) -> str:
    jahr = datetime.now(timezone.utc).year
    n = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
    return f"AP-{jahr}-{n + 1:04d}"


def _audit(conn, inquiry_id: int, action: str, actor: str = "system",
           old: str = "", new: str = "", comment: str = "") -> None:
    conn.execute(
        "INSERT INTO audit_log (inquiry_id, action_type, actor, old_value, new_value, comment, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (inquiry_id, action, actor, old, new, comment, db.now_iso()),
    )


def _finde_duplikat(conn, absender_email: str, betreff: str, nachricht: str) -> str:
    """Einfache Dublettenmarkierung (Modul 1): gleicher Absender + gleicher
    Betreff/Textanfang innerhalb der letzten 14 Tage."""
    if not absender_email:
        return ""
    kennung = (betreff or nachricht[:60]).strip().lower()
    rows = conn.execute(
        "SELECT fall_id, betreff, rohtext FROM inquiries WHERE lower(absender_email) = ?"
        " AND created_at >= datetime('now', '-14 days') ORDER BY id DESC",
        (absender_email.lower(),),
    ).fetchall()
    for row in rows:
        alt = (row["betreff"] or row["rohtext"][:60]).strip().lower()
        if alt and alt == kennung:
            return row["fall_id"]
    return ""


def _analysiere(payload: dict) -> tuple[dict, dict]:
    """Führt die Analyse aus. Liefert (Ergebnis, Metadaten fürs AI-Log)."""
    if llm.llm_verfuegbar():
        try:
            ergebnis = llm.analyse(payload)
            meta = {
                "model": llm.MODEL,
                "prompt_version": llm.PROMPT_VERSION,
                "raw_output": json.dumps(ergebnis, ensure_ascii=False),
                "error": "",
            }
            return ergebnis, meta
        except Exception as exc:  # Fallback: KI-Ausfall blockiert den Eingang nie
            ergebnis = rules.analyse(payload)
            meta = {
                "model": "regelbasiert (LLM-Fallback)",
                "prompt_version": llm.PROMPT_VERSION,
                "raw_output": json.dumps(ergebnis, ensure_ascii=False),
                "error": f"{type(exc).__name__}: {exc}",
            }
            return ergebnis, meta
    ergebnis = rules.analyse(payload)
    meta = {
        "model": "regelbasiert",
        "prompt_version": "rules-v1",
        "raw_output": json.dumps(ergebnis, ensure_ascii=False),
        "error": "",
    }
    return ergebnis, meta


def eingang_verarbeiten(payload: dict) -> dict:
    """Modul 1–6 in einem Durchlauf: Fall anlegen, analysieren, Datensatz füllen.

    payload: kanal, absender_name, absender_email, telefon, betreff, nachricht,
             anhaenge (Liste von Dateinamen).
    """
    nachricht = (payload.get("nachricht") or "").strip()
    if not nachricht:
        raise Eingabefehler("Feld 'nachricht' darf nicht leer sein.")
    kanal = payload.get("kanal") or "formular"
    if kanal not in ("email", "formular"):
        kanal = "formular"
    anhaenge = payload.get("anhaenge") or []
    if isinstance(anhaenge, str):
        anhaenge = [a.strip() for a in anhaenge.split(",") if a.strip()]
    payload = {**payload, "kanal": kanal, "nachricht": nachricht, "anhaenge": anhaenge}

    with db.get_conn() as conn:
        fall_id = _neue_fall_id(conn)
        jetzt = db.now_iso()
        duplikat_von = _finde_duplikat(
            conn, payload.get("absender_email", ""), payload.get("betreff", ""), nachricht
        )
        cur = conn.execute(
            "INSERT INTO inquiries (fall_id, kanal, eingang_ts, absender_name, absender_email,"
            " telefon, betreff, rohtext, anhaenge, status, duplikat_von, letzte_aktion,"
            " created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Neu', ?, 'Fall angelegt', ?, ?)",
            (
                fall_id, kanal, jetzt,
                payload.get("absender_name", ""), payload.get("absender_email", ""),
                payload.get("telefon", ""), payload.get("betreff", ""),
                nachricht, json.dumps(anhaenge, ensure_ascii=False),
                duplikat_von, jetzt, jetzt,
            ),
        )
        inquiry_id = cur.lastrowid
        _audit(conn, inquiry_id, "fall_angelegt", comment=f"Kanal: {kanal}")
        if duplikat_von:
            _audit(conn, inquiry_id, "duplikat_markiert", new=duplikat_von)

        ergebnis, meta = _analysiere(payload)

        if duplikat_von:
            ergebnis["unsicherheiten"] = list(ergebnis.get("unsicherheiten", [])) + [
                f"Mögliche Dublette zu Fall {duplikat_von}."
            ]

        fehlende = ergebnis.get("fehlende_angaben", [])
        freigabe_status = "offen" if ergebnis.get("rueckfrage_entwurf") else "nicht_noetig"
        status = "Vorqualifiziert" if fehlende else "Vollständig"

        conn.execute(
            "UPDATE inquiries SET objektadresse=?, ort=?, gewerk=?, anfrageart=?,"
            " zusammenfassung=?, vorhandene_angaben=?, fehlende_angaben=?,"
            " unsichere_angaben=?, unsicherheiten=?, prioritaet=?, status=?,"
            " rueckfrage_entwurf=?, internes_briefing=?, naechster_schritt=?,"
            " freigabe_status=?, letzte_aktion=?, updated_at=?,"
            " absender_name=CASE WHEN absender_name='' THEN ? ELSE absender_name END,"
            " telefon=CASE WHEN telefon='' THEN ? ELSE telefon END"
            " WHERE id=?",
            (
                ergebnis.get("objektadresse", ""), ergebnis.get("ort", ""),
                ergebnis.get("gewerk", branchen.GEWERK), ergebnis.get("anfrageart", ""),
                ergebnis.get("zusammenfassung", ""),
                json.dumps(ergebnis.get("vorhandene_angaben", []), ensure_ascii=False),
                json.dumps(fehlende, ensure_ascii=False),
                json.dumps(ergebnis.get("unsichere_angaben", []), ensure_ascii=False),
                json.dumps(ergebnis.get("unsicherheiten", []), ensure_ascii=False),
                ergebnis.get("dringlichkeit", "B"), status,
                ergebnis.get("rueckfrage_entwurf", ""),
                ergebnis.get("internes_briefing", ""),
                ergebnis.get("naechster_schritt", ""),
                freigabe_status, "Analyse abgeschlossen", db.now_iso(),
                ergebnis.get("ansprechpartner", ""), ergebnis.get("telefon", ""),
                inquiry_id,
            ),
        )
        conn.execute(
            "INSERT INTO ai_outputs (inquiry_id, output_type, model, prompt_version,"
            " raw_output, error, created_at) VALUES (?, 'analyse', ?, ?, ?, ?, ?)",
            (inquiry_id, meta["model"], meta["prompt_version"], meta["raw_output"],
             meta["error"], db.now_iso()),
        )
        _audit(conn, inquiry_id, "analyse_abgeschlossen", comment=f"Modell: {meta['model']}")

        return fall_laden(conn, fall_id)


def _row_zu_fall(row) -> dict:
    fall = dict(row)
    for feld in ("anhaenge", "vorhandene_angaben", "fehlende_angaben",
                 "unsichere_angaben", "unsicherheiten"):
        try:
            fall[feld] = json.loads(fall.get(feld) or "[]")
        except (TypeError, json.JSONDecodeError):
            fall[feld] = []
    fall["anfrageart_label"] = branchen.anfrageart_label(fall.get("anfrageart", ""))
    return fall


def fall_laden(conn, fall_id: str) -> dict:
    row = conn.execute("SELECT * FROM inquiries WHERE fall_id = ?", (fall_id,)).fetchone()
    if not row:
        raise KeyError(f"Fall {fall_id} nicht gefunden")
    return _row_zu_fall(row)


def fall_holen(fall_id: str) -> dict:
    with db.get_conn() as conn:
        return fall_laden(conn, fall_id)


def faelle_auflisten(status: str = "", prioritaet: str = "", freigabe: str = "") -> list[dict]:
    query = "SELECT * FROM inquiries WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if prioritaet:
        query += " AND prioritaet = ?"
        params.append(prioritaet)
    if freigabe:
        query += " AND freigabe_status = ?"
        params.append(freigabe)
    query += " ORDER BY CASE prioritaet WHEN 'A' THEN 0 WHEN 'B' THEN 1 ELSE 2 END, id DESC"
    with db.get_conn() as conn:
        return [_row_zu_fall(r) for r in conn.execute(query, params).fetchall()]


def kennzahlen() -> dict:
    with db.get_conn() as conn:
        gesamt = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
        offene_freigaben = conn.execute(
            "SELECT COUNT(*) FROM inquiries WHERE freigabe_status = 'offen'"
        ).fetchone()[0]
        prio_a = conn.execute(
            "SELECT COUNT(*) FROM inquiries WHERE prioritaet = 'A'"
            " AND status NOT IN ('Abgeschlossen', 'Verloren / nicht passend')"
        ).fetchone()[0]
        unvollstaendig = conn.execute(
            "SELECT COUNT(*) FROM inquiries WHERE fehlende_angaben != '[]'"
        ).fetchone()[0]
        return {
            "gesamt": gesamt,
            "offene_freigaben": offene_freigaben,
            "prio_a": prio_a,
            "unvollstaendig": unvollstaendig,
        }


def entwurf_speichern(fall_id: str, entwurf: str, actor: str = "büro") -> dict:
    with db.get_conn() as conn:
        fall = fall_laden(conn, fall_id)
        conn.execute(
            "UPDATE inquiries SET rueckfrage_entwurf=?, letzte_aktion='Entwurf bearbeitet',"
            " updated_at=? WHERE fall_id=?",
            (entwurf, db.now_iso(), fall_id),
        )
        _audit(conn, fall["id"], "entwurf_bearbeitet", actor=actor)
        return fall_laden(conn, fall_id)


def entwurf_freigeben(fall_id: str, actor: str = "büro") -> dict:
    """Human-in-the-loop (Modul 4/7): erst nach dieser Freigabe darf der Entwurf
    an den Kunden gehen – die App versendet selbst nichts."""
    with db.get_conn() as conn:
        fall = fall_laden(conn, fall_id)
        neuer_status = fall["status"]
        if fall["status"] in ("Neu", "Vorqualifiziert"):
            neuer_status = "Rückfrage offen"
        conn.execute(
            "UPDATE inquiries SET freigabe_status='freigegeben', status=?,"
            " letzte_aktion='Rückfrageentwurf freigegeben', updated_at=? WHERE fall_id=?",
            (neuer_status, db.now_iso(), fall_id),
        )
        _audit(conn, fall["id"], "entwurf_freigegeben", actor=actor,
               old=fall["status"], new=neuer_status)
        return fall_laden(conn, fall_id)


def entwurf_ablehnen(fall_id: str, kommentar: str = "", actor: str = "büro") -> dict:
    with db.get_conn() as conn:
        fall = fall_laden(conn, fall_id)
        conn.execute(
            "UPDATE inquiries SET freigabe_status='abgelehnt',"
            " letzte_aktion='Entwurf abgelehnt', updated_at=? WHERE fall_id=?",
            (db.now_iso(), fall_id),
        )
        _audit(conn, fall["id"], "entwurf_abgelehnt", actor=actor, comment=kommentar)
        return fall_laden(conn, fall_id)


def status_setzen(fall_id: str, status: str, actor: str = "büro") -> dict:
    if status not in branchen.STATUSWERTE:
        raise Eingabefehler(f"Unbekannter Status: {status}")
    with db.get_conn() as conn:
        fall = fall_laden(conn, fall_id)
        conn.execute(
            "UPDATE inquiries SET status=?, letzte_aktion=?, updated_at=? WHERE fall_id=?",
            (status, f"Status geändert: {status}", db.now_iso(), fall_id),
        )
        _audit(conn, fall["id"], "status_geaendert", actor=actor,
               old=fall["status"], new=status)
        return fall_laden(conn, fall_id)


def verantwortlichen_setzen(fall_id: str, name: str, actor: str = "büro") -> dict:
    with db.get_conn() as conn:
        fall = fall_laden(conn, fall_id)
        conn.execute(
            "UPDATE inquiries SET verantwortlicher=?, updated_at=? WHERE fall_id=?",
            (name.strip(), db.now_iso(), fall_id),
        )
        _audit(conn, fall["id"], "verantwortlicher_gesetzt", actor=actor,
               old=fall["verantwortlicher"], new=name.strip())
        return fall_laden(conn, fall_id)


def audit_fuer_fall(fall_id: str) -> list[dict]:
    with db.get_conn() as conn:
        fall = fall_laden(conn, fall_id)
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE inquiry_id = ? ORDER BY id DESC",
            (fall["id"],),
        ).fetchall()
        return [dict(r) for r in rows]


def ai_outputs_fuer_fall(fall_id: str) -> list[dict]:
    with db.get_conn() as conn:
        fall = fall_laden(conn, fall_id)
        rows = conn.execute(
            "SELECT * FROM ai_outputs WHERE inquiry_id = ? ORDER BY id DESC",
            (fall["id"],),
        ).fetchall()
        return [dict(r) for r in rows]
