"""Lädt 15 synthetische Demo-Anfragen durch die komplette Pipeline.

Entspricht dem Akzeptanzkriterium „mindestens 15 Testfälle stabil laufen“
(Masterdokument 20.3) und dem Demo-Konzept aus Abschnitt 11.

Standard: regelbasierte Analyse (deterministisch, kostenfrei).
Mit --llm wird die Claude-Analyse genutzt, sofern ein API-Key vorhanden ist.
"""

import os
import sys

if "--llm" not in sys.argv:
    os.environ["ANFRAGEPILOT_USE_LLM"] = "off"

from app import service  # noqa: E402

FAELLE = [
    # 1 – Demo-Beispiel aus dem Masterdokument (11.3): Heizungstausch, Fotos da,
    #     aber Wohnfläche/Baujahr/Verbrauch/Wunschsystem/Adresse fehlen.
    dict(kanal="email", absender_name="Familie Becker", absender_email="becker@gmx.de",
         telefon="0176 5551234", betreff="Angebot Heizungstausch",
         nachricht="Guten Tag, wir möchten im Einfamilienhaus in Ettlingen unsere alte "
                   "Gasheizung austauschen. Können Sie uns ein Angebot machen? Im Anhang "
                   "sind zwei Fotos vom Heizraum. Viele Grüße, Familie Becker, Tel. 0176 5551234",
         anhaenge=["heizraum_1.jpg", "heizraum_2.jpg"]),
    # 2 – Heizungstausch, sehr vollständig.
    dict(kanal="formular", absender_name="Petra Wagner", absender_email="p.wagner@web.de",
         telefon="0721 998877", betreff="Wärmepumpe statt Ölheizung",
         nachricht="Hallo, wir planen den Austausch unserer Ölheizung (Baujahr 1998) gegen "
                   "eine Wärmepumpe. Einfamilienhaus in Waldbronn, Bergstraße 12, 76337, "
                   "ca. 140 qm Wohnfläche, Verbrauch ca. 2500 Liter Öl pro Jahr. Umsetzung "
                   "gerne im Sommer. Besichtigung ist jederzeit möglich. Fotos vom Heizraum anbei.",
         anhaenge=["keller.jpg"]),
    # 3 – Notdienst: Rohrbruch, dringend -> Prio A.
    dict(kanal="email", absender_name="Markus Klein", absender_email="m.klein@gmail.com",
         telefon="", betreff="NOTFALL Rohrbruch",
         nachricht="Hilfe, bei uns in Karlsruhe ist ein Rohr geplatzt, im Keller steht "
                   "Wasser! Bitte sofort melden: 0151 2223344. Wir sind den ganzen Tag zu Hause.",
         anhaenge=[]),
    # 4 – Badsanierung, mittlere Vollständigkeit.
    dict(kanal="formular", absender_name="Sabine Vogel", absender_email="vogel.s@t-online.de",
         telefon="07243 55667", betreff="Badsanierung",
         nachricht="Guten Tag, wir möchten unser Bad (ca. 8 qm) in Ettlingen komplett "
                   "sanieren lassen. Wunsch: bodengleiche Dusche und Doppelwaschtisch. "
                   "Gerne Termin zur Besichtigung.",
         anhaenge=[]),
    # 5 – Unklare Anfrage -> Prio C.
    dict(kanal="email", absender_name="", absender_email="info@beispiel-x.de",
         telefon="", betreff="Anfrage",
         nachricht="Hallo, was kostet das bei Ihnen ungefähr? Danke.",
         anhaenge=[]),
    # 6 – Außerhalb Einzugsgebiet -> Prio C.
    dict(kanal="formular", absender_name="Jens Winter", absender_email="j.winter@web.de",
         telefon="0160 7778899", betreff="Heizung erneuern",
         nachricht="Guten Tag, ich möchte in Freiburg meine alte Gasheizung erneuern lassen. "
                   "Reihenhaus, 120 qm. Machen Sie da Angebote?",
         anhaenge=[]),
    # 7 – B2B-Hausverwaltung -> Prio A.
    dict(kanal="email", absender_name="Hausverwaltung Südwest GmbH",
         absender_email="technik@hv-suedwest.de", telefon="0721 445566",
         betreff="Heizungsmodernisierung Objekt Karlsruhe, 12 Wohneinheiten",
         nachricht="Sehr geehrte Damen und Herren, für unsere Liegenschaft in Karlsruhe "
                   "(Mehrfamilienhaus, 12 Wohneinheiten) planen wir die Heizungsmodernisierung "
                   "auf Gas-Brennwert. Bitte um Kontaktaufnahme zwecks Besichtigung und Angebot.",
         anhaenge=["lageplan.pdf"]),
    # 8 – Notdienst: kein Warmwasser (kein Wasseraustritt).
    dict(kanal="formular", absender_name="Anna Sommer", absender_email="a.sommer@gmx.de",
         telefon="0176 8887766", betreff="Kein Warmwasser",
         nachricht="Hallo, unsere Gastherme in Durlach macht seit gestern kein Warmwasser "
                   "mehr. Anzeige blinkt. Wie schnell könnten Sie vorbeikommen?",
         anhaenge=[]),
    # 9 – Badsanierung barrierefrei, wenig Angaben.
    dict(kanal="email", absender_name="Familie Krause", absender_email="krause.fam@gmail.com",
         telefon="", betreff="Barrierefreies Bad für meine Mutter",
         nachricht="Guten Tag, wir suchen jemanden, der das Bad meiner Mutter altersgerecht "
                   "umbaut (Dusche statt Wanne). Sie wohnt in Malsch. Was brauchen Sie von uns?",
         anhaenge=[]),
    # 10 – Heizungstausch mit Förderfrage.
    dict(kanal="formular", absender_name="Tobias Frank", absender_email="t.frank@posteo.de",
         telefon="0157 3334455", betreff="Wärmepumpe + Förderung",
         nachricht="Hallo, wir überlegen, unsere Gastherme (Einfamilienhaus in Rheinstetten, "
                   "Baujahr 1985, 160 qm) durch eine Wärmepumpe zu ersetzen. Gibt es dafür noch "
                   "Förderung? Umsetzung am liebsten im Herbst.",
         anhaenge=[]),
    # 11 – Tropfender Heizkörper, normale Reparatur.
    dict(kanal="email", absender_name="Lisa Brandt", absender_email="l.brandt@web.de",
         telefon="0721 112233", betreff="Heizkörper tropft",
         nachricht="Guten Tag, im Schlafzimmer tropft seit ein paar Tagen der Heizkörper am "
                   "Ventil. Wohnung in Karlsruhe, Rintheimer Straße 8. Wann könnte jemand "
                   "vorbeischauen? Erreichbar ab 16 Uhr.",
         anhaenge=["ventil.jpg"]),
    # 12 – Dublette zu Fall 1 (gleicher Absender, gleicher Betreff).
    dict(kanal="email", absender_name="Familie Becker", absender_email="becker@gmx.de",
         telefon="0176 5551234", betreff="Angebot Heizungstausch",
         nachricht="Guten Tag, ich wollte nur nachfragen, ob unsere Anfrage zum "
                   "Heizungstausch angekommen ist? Viele Grüße, Familie Becker",
         anhaenge=[]),
    # 13 – Verstopfter Abfluss.
    dict(kanal="formular", absender_name="Ömer Yilmaz", absender_email="oe.yilmaz@gmail.com",
         telefon="0163 9990001", betreff="Abfluss verstopft",
         nachricht="Hallo, der Abfluss in der Küche ist komplett verstopft, Wasser läuft "
                   "nicht mehr ab. Wohnung in Ettlingen. Bitte um Rückruf: 0163 9990001.",
         anhaenge=[]),
    # 14 – Badsanierung, sehr vollständig.
    dict(kanal="email", absender_name="Christine & Paul Berger", absender_email="bergers@icloud.com",
         telefon="07243 88990", betreff="Komplettsanierung Bad",
         nachricht="Guten Tag, wir möchten unser Bad in Karlsbad komplett sanieren: ca. 10 qm, "
                   "bodengleiche Dusche, neue Badewanne, Fliesen und Fußbodenheizung. Fotos vom "
                   "Bestand im Anhang. Zeitraum: Frühjahr nächstes Jahr. Besichtigung gerne "
                   "nach 17 Uhr, Tel. 07243 88990.",
         anhaenge=["bad_ist_1.jpg", "bad_ist_2.jpg", "grundriss.pdf"]),
    # 15 – Heizungsausfall im Winter -> Prio A.
    dict(kanal="email", absender_name="Robert Held", absender_email="r.held@t-online.de",
         telefon="", betreff="Heizung komplett ausgefallen",
         nachricht="Guten Abend, unsere Heizung in Pfinztal ist komplett ausgefallen, die "
                   "Wohnung wird nicht mehr warm. Das eilt, wir haben ein Baby zu Hause. "
                   "Bitte dringend melden: 0170 4445566.",
         anhaenge=[]),
]


def main() -> None:
    angelegt = []
    for payload in FAELLE:
        fall = service.eingang_verarbeiten(payload)
        angelegt.append(fall)
        print(f"  {fall['fall_id']}  Prio {fall['prioritaet']}  "
              f"{fall['anfrageart_label']:<22} {fall['status']:<16} "
              f"fehlend: {len(fall['fehlende_angaben'])}")

    # Ein paar Bearbeitungsschritte simulieren, damit Dashboard & Report leben:
    service.entwurf_freigeben(angelegt[0]["fall_id"])            # Becker
    service.entwurf_freigeben(angelegt[3]["fall_id"])            # Vogel
    service.entwurf_freigeben(angelegt[8]["fall_id"])            # Krause
    service.status_setzen(angelegt[1]["fall_id"], "Bereit für Angebot")
    service.status_setzen(angelegt[6]["fall_id"], "In Bearbeitung")
    service.verantwortlichen_setzen(angelegt[6]["fall_id"], "Meister M.")
    service.status_setzen(angelegt[5]["fall_id"], "Verloren / nicht passend")
    service.entwurf_ablehnen(angelegt[4]["fall_id"],
                             kommentar="Zu unklar – telefonisch klären.")

    print(f"\n{len(angelegt)} Demo-Fälle angelegt. Dashboard: uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
