"""End-to-End-Tests der Pipeline über die HTTP-API (Webhook + Freigabe-Flow).

Deckt die MVP-Akzeptanzkriterien aus Abschnitt 20.3 ab, u. a.
„mindestens 15 Testfälle stabil laufen“.
"""

import importlib
import os
import sys
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path):
    os.environ["ANFRAGEPILOT_USE_LLM"] = "off"
    os.environ["ANFRAGEPILOT_DB"] = str(tmp_path / "test.db")
    from app import main
    importlib.reload(main)
    return TestClient(main.app)


def _anfrage(client, **kwargs):
    payload = {
        "kanal": "email",
        "absender_name": "Familie Becker",
        "absender_email": "becker@gmx.de",
        "telefon": "0176 5551234",
        "betreff": "Angebot Heizungstausch",
        "nachricht": "Wir möchten im Einfamilienhaus in Ettlingen unsere alte Gasheizung "
                     "austauschen. Fotos vom Heizraum im Anhang.",
        "anhaenge": ["heizraum_1.jpg"],
    }
    payload.update(kwargs)
    return client.post("/api/anfragen", json=payload)


def test_webhook_legt_fall_an(client):
    r = _anfrage(client)
    assert r.status_code == 201
    daten = r.json()
    assert daten["fall_id"].startswith("AP-")
    assert daten["anfrageart"] == "heizungstausch"
    assert daten["status"] == "Vorqualifiziert"
    assert daten["freigabe_status"] == "offen"
    assert len(daten["fehlende_angaben"]) > 0


def test_leere_nachricht_wird_abgelehnt(client):
    r = _anfrage(client, nachricht="   ")
    assert r.status_code == 400


def test_dashboard_und_detailseite(client):
    fall_id = _anfrage(client).json()["fall_id"]
    r = client.get("/")
    assert r.status_code == 200
    assert fall_id in r.text
    r = client.get(f"/fall/{fall_id}")
    assert r.status_code == 200
    assert "Rückfrageentwurf" in r.text
    assert "Internes Angebots-Briefing" in r.text


def test_freigabe_flow(client):
    fall_id = _anfrage(client).json()["fall_id"]

    # Entwurf bearbeiten
    r = client.post(f"/fall/{fall_id}/entwurf",
                    data={"entwurf": "Guten Tag, bitte noch die Adresse. [Betrieb]"},
                    follow_redirects=False)
    assert r.status_code == 303

    # Freigeben -> Status „Rückfrage offen“
    r = client.post(f"/fall/{fall_id}/freigabe", data={"aktion": "freigeben"},
                    follow_redirects=False)
    assert r.status_code == 303
    fall = client.get(f"/api/anfragen/{fall_id}").json()
    assert fall["freigabe_status"] == "freigegeben"
    assert fall["status"] == "Rückfrage offen"
    assert fall["rueckfrage_entwurf"].startswith("Guten Tag, bitte noch die Adresse.")


def test_manuelle_statusaenderung(client):
    fall_id = _anfrage(client).json()["fall_id"]
    r = client.post(f"/fall/{fall_id}/status", data={"status": "Bereit für Angebot"},
                    follow_redirects=False)
    assert r.status_code == 303
    fall = client.get(f"/api/anfragen/{fall_id}").json()
    assert fall["status"] == "Bereit für Angebot"

    r = client.post(f"/fall/{fall_id}/status", data={"status": "Quatschstatus"},
                    follow_redirects=False)
    assert r.status_code == 400


def test_dublettenerkennung(client):
    erster = _anfrage(client).json()["fall_id"]
    zweiter = _anfrage(client).json()["fall_id"]
    fall = client.get(f"/api/anfragen/{zweiter}").json()
    assert fall["duplikat_von"] == erster


def test_ai_output_logging(client):
    fall_id = _anfrage(client).json()["fall_id"]
    r = client.get(f"/fall/{fall_id}")
    assert "regelbasiert" in r.text  # Modell im KI-Output-Log sichtbar


def test_15_demo_faelle_laufen_stabil(client, monkeypatch):
    """Akzeptanzkriterium 20.3: mindestens 15 Testfälle laufen stabil durch."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import seed_demo
    for payload in seed_demo.FAELLE:
        r = client.post("/api/anfragen", json=payload)
        assert r.status_code == 201, f"Fall fehlgeschlagen: {payload['betreff']}"
    assert len(seed_demo.FAELLE) >= 15

    # Jeder Fall hat Zusammenfassung, Briefing, Priorität und Status.
    uebersicht = client.get("/")
    assert uebersicht.status_code == 200
    jahr = datetime.now(timezone.utc).year
    for i in range(1, 16):
        fall = client.get(f"/api/anfragen/AP-{jahr}-{i:04d}").json()
        assert fall["zusammenfassung"], f"Fall {i} ohne Zusammenfassung"
        assert fall["internes_briefing"], f"Fall {i} ohne Briefing"
        assert fall["prioritaet"] in ("A", "B", "C")
        assert fall["status"] in ("Vorqualifiziert", "Vollständig")

    # Report funktioniert mit Daten.
    r = client.get("/report")
    assert r.status_code == 200
