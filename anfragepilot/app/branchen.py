"""Branchenkonfiguration für den MVP-Piloten.

Ein Mandant, eine Vertikale (SHK), drei Anfragearten – wie im Masterdokument
(Abschnitte 7.1 / 20.2) vorgegeben. Die Pflichtfeldliste für den Heizungstausch
stammt direkt aus Abschnitt 8.1; die beiden anderen Anfragearten folgen derselben
Systematik.
"""

GEWERK = "SHK (Sanitär, Heizung, Klima)"

BETRIEB = {
    "name": "Muster Haustechnik GmbH",
    "region": "Karlsruhe / Ettlingen / Waldbronn",
}

# Einzugsgebiet des Pilotbetriebs. Orte außerhalb -> Priorität C + Unsicherheit.
EINZUGSGEBIET = [
    "Karlsruhe",
    "Ettlingen",
    "Waldbronn",
    "Karlsbad",
    "Rheinstetten",
    "Pfinztal",
    "Malsch",
    "Durlach",
    "Marxzell",
    "Remchingen",
    "Weingarten",
    "Stutensee",
    "Bruchsal",
]

STATUSWERTE = [
    "Neu",
    "Vorqualifiziert",
    "Rückfrage offen",
    "Vollständig",
    "Bereit für Angebot",
    "In Bearbeitung",
    "Abgeschlossen",
    "Verloren / nicht passend",
]

PRIORITAETEN = ["A", "B", "C"]

FREIGABE_STATUS = ["offen", "freigegeben", "abgelehnt", "nicht_noetig"]

# Pflichtfelder: key = Detektor-Name (rules.py), label = Anzeige,
# frage = Formulierung für den Rückfrageentwurf.
ANFRAGEARTEN = {
    "heizungstausch": {
        "label": "Heizungstausch",
        "keywords": [
            "heizungstausch", "heizung tauschen", "heizung austauschen",
            "heizung erneuern", "heizung ersetzen", "neue heizung",
            "heizungsmodernisierung", "wärmepumpe", "waermepumpe",
            "gasheizung austauschen", "ölheizung raus", "heizungsangebot",
        ],
        "pflichtfelder": [
            {"key": "objektadresse", "label": "Vollständige Objektadresse",
             "frage": "die vollständige Objektadresse (Straße, Hausnummer, PLZ, Ort)"},
            {"key": "gebaeudeart", "label": "Gebäudeart",
             "frage": "die Gebäudeart (z. B. Einfamilienhaus, Mehrfamilienhaus, Wohnung)"},
            {"key": "wohnflaeche", "label": "Wohnfläche",
             "frage": "die ungefähre Wohnfläche in m²"},
            {"key": "baujahr", "label": "Baujahr des Gebäudes",
             "frage": "das Baujahr des Gebäudes"},
            {"key": "aktuelles_heizsystem", "label": "Aktuelles Heizsystem",
             "frage": "das aktuelle Heizsystem inkl. Typbezeichnung, falls bekannt"},
            {"key": "energieverbrauch", "label": "Aktueller Energieverbrauch",
             "frage": "den ungefähren jährlichen Energieverbrauch (kWh Gas oder Liter Öl)"},
            {"key": "neues_heizsystem", "label": "Gewünschtes neues Heizsystem",
             "frage": "das gewünschte neue Heizsystem (z. B. Wärmepumpe, Gas-Brennwert)"},
            {"key": "fotos", "label": "Fotos vom Heizraum",
             "frage": "einige Fotos vom Heizraum und der bestehenden Anlage"},
            {"key": "zeitraum", "label": "Gewünschter Zeitraum",
             "frage": "den gewünschten Umsetzungszeitraum"},
            {"key": "ansprechpartner", "label": "Ansprechpartner",
             "frage": "einen Ansprechpartner für Rückfragen"},
            {"key": "telefon", "label": "Telefonnummer",
             "frage": "eine Telefonnummer für Rückfragen"},
            {"key": "besichtigung", "label": "Besichtigung möglich ja/nein",
             "frage": "ob eine Vor-Ort-Besichtigung möglich wäre"},
        ],
        "checkliste": [
            "Bestandsanlage: Typenschild / Baujahr klären",
            "Förderfähigkeit (BEG) prüfen und ansprechen",
            "Hydraulik / Heizkörper vs. Flächenheizung bewerten",
            "Vor-Ort-Termin für Aufmaß einplanen",
            "Lieferzeiten Wunschsystem prüfen",
        ],
    },
    "badsanierung": {
        "label": "Badsanierung",
        "keywords": [
            "badsanierung", "bad sanieren", "bad renovieren", "badumbau",
            "bad umbauen", "neues bad", "badezimmer sanieren",
            "badezimmer renovieren", "barrierefreies bad", "dusche statt wanne",
            "bodengleiche dusche",
        ],
        "pflichtfelder": [
            {"key": "objektadresse", "label": "Vollständige Objektadresse",
             "frage": "die vollständige Objektadresse (Straße, Hausnummer, PLZ, Ort)"},
            {"key": "badgroesse", "label": "Badgröße",
             "frage": "die ungefähre Größe des Bads in m²"},
            {"key": "umfang", "label": "Gewünschter Sanierungsumfang",
             "frage": "den gewünschten Umfang (Komplettsanierung oder Teilbereiche)"},
            {"key": "ausstattung", "label": "Ausstattungswünsche",
             "frage": "Ihre Ausstattungswünsche (z. B. bodengleiche Dusche, Badewanne, Doppelwaschtisch)"},
            {"key": "fotos", "label": "Fotos vom Bestand",
             "frage": "einige Fotos vom aktuellen Bad"},
            {"key": "zeitraum", "label": "Gewünschter Zeitraum",
             "frage": "den gewünschten Umsetzungszeitraum"},
            {"key": "ansprechpartner", "label": "Ansprechpartner",
             "frage": "einen Ansprechpartner für Rückfragen"},
            {"key": "telefon", "label": "Telefonnummer",
             "frage": "eine Telefonnummer für Rückfragen"},
            {"key": "besichtigung", "label": "Besichtigung möglich ja/nein",
             "frage": "ob eine Vor-Ort-Besichtigung möglich wäre"},
        ],
        "checkliste": [
            "Grundriss / Maße anfordern oder Aufmaß planen",
            "Gewerkeschnittstellen klären (Fliesen, Elektro)",
            "Vorwandinstallation / Leitungsführung prüfen",
            "Ausstattungsbudget grob abklopfen",
            "Vor-Ort-Termin einplanen",
        ],
    },
    "reparatur_notdienst": {
        "label": "Reparatur / Notdienst",
        "keywords": [
            "notdienst", "notfall", "rohrbruch", "wasserschaden", "undicht",
            "tropft", "verstopft", "verstopfung", "abfluss", "heizung ausgefallen",
            "heizungsausfall", "kein warmwasser", "keine heizung", "defekt",
            "kaputt", "reparatur", "läuft aus", "druck fällt", "ausgefallen",
            "nicht mehr warm", "wird nicht warm",
        ],
        "pflichtfelder": [
            {"key": "objektadresse", "label": "Objektadresse",
             "frage": "die genaue Objektadresse (Straße, Hausnummer, PLZ, Ort)"},
            {"key": "problembeschreibung", "label": "Fehler-/Problembeschreibung",
             "frage": "eine kurze Beschreibung des Problems"},
            {"key": "betroffenes_geraet", "label": "Betroffenes Gerät/System",
             "frage": "welches Gerät bzw. welche Anlage betroffen ist (z. B. Therme, Heizkörper, Abfluss)"},
            {"key": "seit_wann", "label": "Seit wann besteht das Problem",
             "frage": "seit wann das Problem besteht"},
            {"key": "wasseraustritt", "label": "Wasseraustritt ja/nein",
             "frage": "ob aktuell Wasser austritt"},
            {"key": "telefon", "label": "Rückrufnummer",
             "frage": "eine Telefonnummer, unter der wir Sie kurzfristig erreichen"},
            {"key": "erreichbarkeit", "label": "Erreichbarkeit / Zugang",
             "frage": "wann jemand vor Ort erreichbar ist"},
        ],
        "checkliste": [
            "Dringlichkeit telefonisch verifizieren",
            "Bei Wasseraustritt: Absperrhinweis geben",
            "Monteurverfügbarkeit prüfen",
            "Anfahrt / Notdienstpauschale transparent machen",
        ],
    },
}

ANFRAGEART_UNKLAR = "unklar"


def anfrageart_label(key: str) -> str:
    if key in ANFRAGEARTEN:
        return ANFRAGEARTEN[key]["label"]
    return "Unklar / Sonstiges"
