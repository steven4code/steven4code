"""Tests für die regelbasierte Analyse (Klassifikation, Missing Fields, Prio)."""

import os

os.environ["ANFRAGEPILOT_USE_LLM"] = "off"

from app import rules  # noqa: E402

BECKER = {
    "kanal": "email",
    "absender_name": "Familie Becker",
    "absender_email": "becker@gmx.de",
    "telefon": "0176 5551234",
    "betreff": "Angebot Heizungstausch",
    "nachricht": (
        "Guten Tag, wir möchten im Einfamilienhaus in Ettlingen unsere alte "
        "Gasheizung austauschen. Können Sie uns ein Angebot machen? Im Anhang "
        "sind zwei Fotos vom Heizraum. Viele Grüße, Familie Becker, Tel. 0176 5551234"
    ),
    "anhaenge": ["heizraum_1.jpg", "heizraum_2.jpg"],
}


def test_becker_beispiel_aus_masterdokument():
    """Erwartetes Verhalten aus Abschnitt 11.3 des Masterdokuments."""
    e = rules.analyse(BECKER)
    assert e["anfrageart"] == "heizungstausch"
    assert e["ort"] == "Ettlingen"
    assert e["dringlichkeit"] == "B"
    labels_fehlend = e["fehlende_angaben"]
    for erwartet in ("Wohnfläche", "Baujahr des Gebäudes", "Aktueller Energieverbrauch",
                     "Gewünschtes neues Heizsystem", "Gewünschter Zeitraum",
                     "Vollständige Objektadresse"):
        assert erwartet in labels_fehlend, f"{erwartet} sollte als fehlend erkannt werden"
    vorhandene_felder = [a["feld"] for a in e["vorhandene_angaben"]]
    assert "Fotos vom Heizraum" in vorhandene_felder
    assert "Telefonnummer" in vorhandene_felder
    assert "Aktuelles Heizsystem" in vorhandene_felder
    assert e["rueckfrage_entwurf"]
    assert e["internes_briefing"]


def test_rueckfrage_regeln():
    """Abschnitt 10.3: max. ~140 Wörter, keine Preise, Signatur-Platzhalter."""
    e = rules.analyse(BECKER)
    entwurf = e["rueckfrage_entwurf"]
    assert len(entwurf.split()) <= 150
    assert "€" not in entwurf and "Preis" not in entwurf and "kostet" not in entwurf
    assert "[Betrieb]" in entwurf
    assert entwurf.startswith("Guten Tag Familie Becker,")


def test_notdienst_wird_prio_a():
    e = rules.analyse({
        "kanal": "email", "absender_name": "Markus Klein",
        "absender_email": "m.klein@gmail.com",
        "betreff": "NOTFALL Rohrbruch",
        "nachricht": "Bei uns in Karlsruhe ist ein Rohr geplatzt, im Keller steht Wasser! "
                     "Bitte sofort melden: 0151 2223344.",
        "anhaenge": [],
    })
    assert e["anfrageart"] == "reparatur_notdienst"
    assert e["dringlichkeit"] == "A"
    assert "Sofort telefonisch" in e["naechster_schritt"]


def test_ausserhalb_einzugsgebiet_wird_prio_c():
    e = rules.analyse({
        "kanal": "formular", "absender_name": "Jens Winter",
        "absender_email": "j.winter@web.de",
        "betreff": "Heizung erneuern",
        "nachricht": "Ich möchte in Freiburg meine alte Gasheizung erneuern lassen.",
        "anhaenge": [],
    })
    assert e["dringlichkeit"] == "C"
    assert any("Einzugsgebiet" in u for u in e["unsicherheiten"])


def test_unklare_anfrage_wird_prio_c():
    e = rules.analyse({
        "kanal": "email", "absender_name": "", "absender_email": "x@beispiel.de",
        "betreff": "Anfrage", "nachricht": "Hallo, was kostet das ungefähr?", "anhaenge": [],
    })
    assert e["anfrageart"] == "unklar"
    assert e["dringlichkeit"] == "C"
    assert "Konkrete Leistungsbeschreibung" in e["fehlende_angaben"]


def test_badsanierung_klassifikation():
    e = rules.analyse({
        "kanal": "formular", "absender_name": "Sabine Vogel",
        "absender_email": "vogel.s@t-online.de", "telefon": "07243 55667",
        "betreff": "Badsanierung",
        "nachricht": "Wir möchten unser Bad (ca. 8 qm) in Ettlingen komplett sanieren "
                     "lassen. Wunsch: bodengleiche Dusche.",
        "anhaenge": [],
    })
    assert e["anfrageart"] == "badsanierung"
    felder = [a["feld"] for a in e["vorhandene_angaben"]]
    assert "Badgröße" in felder
    assert "Gewünschter Sanierungsumfang" in felder


def test_vollstaendige_anfrage_ohne_rueckfrage():
    e = rules.analyse({
        "kanal": "email", "absender_name": "Petra Wagner",
        "absender_email": "p.wagner@web.de", "telefon": "0721 998877",
        "betreff": "Wärmepumpe statt Ölheizung",
        "nachricht": "Wir planen den Austausch unserer Ölheizung (Baujahr 1998) gegen eine "
                     "Wärmepumpe. Einfamilienhaus in Waldbronn, Bergstraße 12, 76337 Waldbronn, "
                     "ca. 140 qm Wohnfläche, Verbrauch ca. 2500 Liter Öl pro Jahr. Umsetzung im "
                     "Sommer. Besichtigung jederzeit möglich. Fotos anbei.",
        "anhaenge": ["keller.jpg"],
    })
    assert e["anfrageart"] == "heizungstausch"
    assert e["fehlende_angaben"] == []
    assert e["rueckfrage_entwurf"] == ""
