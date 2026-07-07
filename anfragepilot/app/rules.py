"""Regelbasierte Analyse als deterministischer Fallback zur LLM-Analyse.

Liefert dieselbe Ergebnisstruktur wie app.llm.analyse(), damit die Pipeline
auch ohne API-Zugang (Demo, Tests, Ausfall) vollständig funktioniert.
"""

from __future__ import annotations

import re

from . import branchen

PHONE_RE = re.compile(r"(?:\+49|0)[\d][\d /\-().]{6,}\d")
STREET_RE = re.compile(
    r"[A-ZÄÖÜ][\wäöüß.\-]*(?:straße|strasse|str\.|weg|platz|allee|gasse|ring|damm)\s*\.?\s*\d+\s*\w?",
    re.IGNORECASE,
)
PLZ_ORT_RE = re.compile(r"\b(\d{5})\s+([A-ZÄÖÜ][a-zäöüß\-]+)")
AREA_RE = re.compile(r"\b\d{1,4}\s*(?:qm|m2|m²|quadratmeter)\b", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(?:baujahr|bj\.?|gebaut)\s*:?\s*((?:19|20)\d{2})\b", re.IGNORECASE)
CONSUMPTION_RE = re.compile(
    r"\b\d[\d.,]*\s*(?:kwh|kilowattstunden|liter(?:\s+(?:öl|heizöl))?|m³|kubikmeter)\b",
    re.IGNORECASE,
)
SEIT_RE = re.compile(r"\bseit\s+\w+(?:\s\w+)?", re.IGNORECASE)

FREEMAIL_DOMAINS = (
    "gmail.", "googlemail.", "web.de", "gmx.", "t-online.", "outlook.",
    "hotmail.", "yahoo.", "icloud.", "freenet.", "posteo.", "mail.de",
)

B2B_HINWEISE = [
    "gmbh", "ag ", "kg ", "ohg", "ug (", "hausverwaltung", "wohnungsbau",
    "immobilien", "facility", "objektbetreuung", "firma", "unternehmen",
    "gewerbe", "verwaltung",
]

NOTFALL_HINWEISE = [
    "notdienst", "notfall", "dringend", "sofort", "so schnell wie möglich",
    "schnellstmöglich", "eilt", "rohrbruch", "wasserschaden", "heizungsausfall",
    "heizung ausgefallen", "keine heizung", "kein warmwasser", "läuft aus",
    "steht unter wasser",
]

ZEITRAUM_HINWEISE = [
    "januar", "februar", "märz", "april", "mai", "juni", "juli", "august",
    "september", "oktober", "november", "dezember", "frühjahr", "fruehjahr",
    "sommer", "herbst", "winter", "sofort", "demnächst", "zeitnah",
    "nächste woche", "nächsten monat", "dieses jahr", "nächstes jahr",
    "kw ", "bis ende", "ab sofort",
]

GEBAEUDEART_HINWEISE = [
    "einfamilienhaus", "efh", "mehrfamilienhaus", "mfh", "doppelhaushälfte",
    "doppelhaus", "reihenhaus", "wohnung", "eigentumswohnung", "altbau",
    "neubau", "bürogebäude", "gewerbehalle", "gewerbeobjekt",
]

HEIZSYSTEM_BESTAND = [
    "gasheizung", "gastherme", "gaskessel", "gas-heizung", "ölheizung",
    "oelheizung", "öltherme", "ölkessel", "öl-zentralheizung",
    "nachtspeicher", "fernwärme", "elektroheizung", "gasetagenheizung",
]

HEIZSYSTEM_NEU = [
    "wärmepumpe", "waermepumpe", "luft-wasser", "sole-wasser",
    "pelletheizung", "pellets", "brennwerttherme", "gas-brennwert",
    "hybridheizung", "solarthermie", "fernwärmeanschluss",
]

AUSSTATTUNG_HINWEISE = [
    "bodengleiche dusche", "walk-in", "badewanne", "doppelwaschtisch",
    "regendusche", "wc", "fliesen", "fußbodenheizung", "handtuchheizkörper",
    "barrierefrei", "altersgerecht",
]

UMFANG_HINWEISE = [
    "komplettsanierung", "komplett sanieren", "komplett renovieren",
    "kernsanierung", "teilsanierung", "nur die dusche", "nur dusche",
    "wanne raus", "dusche statt wanne", "alles neu",
]

GERAETE_HINWEISE = [
    "therme", "gastherme", "heizung", "heizkörper", "kessel", "boiler",
    "durchlauferhitzer", "warmwasserspeicher", "abfluss", "rohr", "leitung",
    "waschbecken", "toilette", "spülkasten", "dusche", "armatur", "pumpe",
]

PROBLEM_HINWEISE = [
    "tropft", "undicht", "rohrbruch", "wasserschaden", "ausgefallen",
    "defekt", "kaputt", "verstopft", "verstopfung", "läuft aus",
    "läuft nicht", "kein warmwasser", "keine heizung", "wird nicht warm",
    "nicht mehr warm", "druck fällt", "macht geräusche", "klopft", "leckt",
]

WASSER_HINWEISE = [
    "läuft wasser", "wasser läuft", "tropft", "wasserschaden", "rohrbruch",
    "steht unter wasser", "überschwemmt", "läuft aus", "leckt",
]


def _find_keyword(text_lower: str, keywords: list[str]) -> str | None:
    for kw in keywords:
        if kw in text_lower:
            return kw
    return None


def klassifiziere_anfrageart(text: str) -> str:
    text_lower = text.lower()
    # Notdienst-Signale schlagen andere Treffer (dringlicher Fall zuerst).
    if _find_keyword(text_lower, branchen.ANFRAGEARTEN["reparatur_notdienst"]["keywords"]):
        # "Reparatur"-Worte in einer klaren Tausch-Anfrage nicht überbewerten:
        tausch = _find_keyword(text_lower, branchen.ANFRAGEARTEN["heizungstausch"]["keywords"])
        problem = _find_keyword(text_lower, PROBLEM_HINWEISE) or _find_keyword(text_lower, NOTFALL_HINWEISE)
        if not tausch or problem:
            return "reparatur_notdienst"
    for art in ("heizungstausch", "badsanierung"):
        if _find_keyword(text_lower, branchen.ANFRAGEARTEN[art]["keywords"]):
            return art
    return branchen.ANFRAGEART_UNKLAR


def erkenne_ort(text: str) -> tuple[str | None, bool]:
    """Liefert (Ort, im_einzugsgebiet)."""
    for ort in branchen.EINZUGSGEBIET:
        if re.search(rf"\b{re.escape(ort)}\b", text, re.IGNORECASE):
            return ort, True
    m = PLZ_ORT_RE.search(text)
    if m:
        return f"{m.group(1)} {m.group(2)}", False
    m = re.search(r"\bin\s+([A-ZÄÖÜ][a-zäöüß\-]{3,})\b", text)
    if m and m.group(1).lower() not in ("anhang", "unserem", "unserer", "ihrem", "ihrer"):
        return m.group(1), False
    return None, False


# --- Feld-Detektoren -------------------------------------------------------
# Jeder Detektor bekommt den Fall-Kontext und liefert den erkannten Wert
# (oder None, wenn die Angabe fehlt).

def _det_objektadresse(ctx: dict) -> str | None:
    m = STREET_RE.search(ctx["text"])
    if m:
        plz = PLZ_ORT_RE.search(ctx["text"])
        return f"{m.group(0).strip()}" + (f", {plz.group(0)}" if plz else "")
    return None


def _det_ort_vorhanden(ctx: dict) -> str | None:
    return ctx["ort"]


def _det_gebaeudeart(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], GEBAEUDEART_HINWEISE)


def _det_wohnflaeche(ctx: dict) -> str | None:
    m = AREA_RE.search(ctx["text"])
    return m.group(0) if m else None


def _det_baujahr(ctx: dict) -> str | None:
    m = YEAR_RE.search(ctx["text"])
    return m.group(1) if m else None


def _det_heizsystem_bestand(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], HEIZSYSTEM_BESTAND)


def _det_energieverbrauch(ctx: dict) -> str | None:
    m = CONSUMPTION_RE.search(ctx["text"])
    return m.group(0) if m else None


def _det_heizsystem_neu(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], HEIZSYSTEM_NEU)


def _det_fotos(ctx: dict) -> str | None:
    if ctx["anhaenge"]:
        return f"{len(ctx['anhaenge'])} Anhang/Anhänge"
    if _find_keyword(ctx["text_lower"], ["foto", "bilder", "im anhang", "anbei"]):
        return "Fotos laut Text angekündigt"
    return None


def _det_zeitraum(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], ZEITRAUM_HINWEISE)


def _det_ansprechpartner(ctx: dict) -> str | None:
    return ctx["absender_name"] or None


def _det_telefon(ctx: dict) -> str | None:
    if ctx["telefon"]:
        return ctx["telefon"]
    m = PHONE_RE.search(ctx["text"])
    return m.group(0).strip() if m else None


def _det_besichtigung(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], ["besichtigung", "vor-ort-termin", "vor ort", "gerne vorbeikommen"])


def _det_badgroesse(ctx: dict) -> str | None:
    return _det_wohnflaeche(ctx)


def _det_umfang(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], UMFANG_HINWEISE)


def _det_ausstattung(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], AUSSTATTUNG_HINWEISE)


def _det_problembeschreibung(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], PROBLEM_HINWEISE)


def _det_betroffenes_geraet(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], GERAETE_HINWEISE)


def _det_seit_wann(ctx: dict) -> str | None:
    m = SEIT_RE.search(ctx["text"])
    if m:
        return m.group(0)
    return _find_keyword(ctx["text_lower"], ["plötzlich", "gerade eben", "heute morgen", "heute früh"])


def _det_wasseraustritt(ctx: dict) -> str | None:
    return _find_keyword(ctx["text_lower"], WASSER_HINWEISE)


def _det_erreichbarkeit(ctx: dict) -> str | None:
    tel = _det_telefon(ctx)
    if tel:
        return f"telefonisch: {tel}"
    return _find_keyword(ctx["text_lower"], ["erreichbar", "zu hause", "vor ort"])


DETEKTOREN = {
    "objektadresse": _det_objektadresse,
    "gebaeudeart": _det_gebaeudeart,
    "wohnflaeche": _det_wohnflaeche,
    "baujahr": _det_baujahr,
    "aktuelles_heizsystem": _det_heizsystem_bestand,
    "energieverbrauch": _det_energieverbrauch,
    "neues_heizsystem": _det_heizsystem_neu,
    "fotos": _det_fotos,
    "zeitraum": _det_zeitraum,
    "ansprechpartner": _det_ansprechpartner,
    "telefon": _det_telefon,
    "besichtigung": _det_besichtigung,
    "badgroesse": _det_badgroesse,
    "umfang": _det_umfang,
    "ausstattung": _det_ausstattung,
    "problembeschreibung": _det_problembeschreibung,
    "betroffenes_geraet": _det_betroffenes_geraet,
    "seit_wann": _det_seit_wann,
    "wasseraustritt": _det_wasseraustritt,
    "erreichbarkeit": _det_erreichbarkeit,
}


def bestimme_prioritaet(anfrageart: str, text_lower: str, ort: str | None,
                        im_gebiet: bool, absender_email: str, absender_name: str) -> tuple[str, str]:
    """Liefert (Priorität, Begründung) nach der A/B/C-Logik aus Modul 6."""
    if ort and not im_gebiet:
        return "C", f"Objektort „{ort}“ liegt vermutlich außerhalb des Einzugsgebiets."
    if anfrageart == branchen.ANFRAGEART_UNKLAR:
        return "C", "Anfrageart unklar – Passung erst nach Rückfrage bewertbar."
    if _find_keyword(text_lower, NOTFALL_HINWEISE):
        return "A", "Dringlichkeits-/Notdienstsignale im Text erkannt."
    b2b_text = (absender_name + " " + text_lower).lower()
    domain = absender_email.split("@")[-1].lower() if "@" in absender_email else ""
    gewerblich = _find_keyword(b2b_text, B2B_HINWEISE) or (
        domain and not any(domain.startswith(d) or d in domain for d in FREEMAIL_DOMAINS)
    )
    if gewerblich and _find_keyword(text_lower, ["objekt", "wohneinheiten", "liegenschaft", "verwaltung", "gmbh"]):
        return "A", "Gewerblicher Absender / B2B-Anfrage mit potenziell hohem Wert."
    return "B", "Normale, bearbeitbare Anfrage ohne Sonderdringlichkeit."


def baue_rueckfrage(absender_name: str, fragen: list[str]) -> str:
    """Rückfrageentwurf nach den Regeln aus Abschnitt 10.3 (max. ~140 Wörter,
    keine Preis-/Terminzusagen, nur tatsächlich fehlende Angaben)."""
    anrede = f"Guten Tag {absender_name}," if absender_name else "Guten Tag,"
    fragen = fragen[:7]
    zeilen = "\n".join(f"- {f}" for f in fragen)
    return (
        f"{anrede}\n\n"
        "vielen Dank für Ihre Anfrage. Damit wir Ihr Anliegen gut einschätzen "
        "können, benötigen wir noch folgende Angaben:\n\n"
        f"{zeilen}\n\n"
        "Sobald uns diese Informationen vorliegen, melden wir uns zeitnah mit "
        "den nächsten Schritten.\n\n"
        "Freundliche Grüße\n"
        "[Betrieb]"
    )


def baue_briefing(daten: dict) -> str:
    """Internes Angebots-Briefing (Modul 5)."""
    vorhandene = "\n".join(
        f"  - {a['feld']}: {a['wert']}" for a in daten["vorhandene_angaben"]
    ) or "  - (keine strukturiert erkannten Angaben)"
    fehlende = "\n".join(f"  - {f}" for f in daten["fehlende_angaben"]) or "  - keine"
    unsicher = "\n".join(f"  - {u}" for u in daten["unsicherheiten"]) or "  - keine"
    checkliste = "\n".join(f"  [ ] {c}" for c in daten["checkliste"]) or "  (keine)"
    return (
        f"INTERNES ANGEBOTS-BRIEFING\n"
        f"==========================\n"
        f"Zusammenfassung: {daten['zusammenfassung']}\n\n"
        f"Kunde/Kontakt:  {daten['kontakt']}\n"
        f"Objekt/Ort:     {daten['ort'] or 'unbekannt'}\n"
        f"Gewerk:         {branchen.GEWERK}\n"
        f"Anfrageart:     {daten['anfrageart_label']}\n"
        f"Priorität:      {daten['prioritaet']} – {daten['prio_begruendung']}\n\n"
        f"Bekannte Angaben:\n{vorhandene}\n\n"
        f"Fehlende Angaben:\n{fehlende}\n\n"
        f"Risiken / Unsicherheiten:\n{unsicher}\n\n"
        f"Empfohlener nächster Schritt: {daten['naechster_schritt']}\n\n"
        f"Interne Checkliste:\n{checkliste}"
    )


def analyse(payload: dict) -> dict:
    """Vollständige regelbasierte Analyse. Gleiche Struktur wie llm.analyse()."""
    text = " ".join(
        s for s in (payload.get("betreff", ""), payload.get("nachricht", "")) if s
    )
    text_lower = text.lower()
    anhaenge = payload.get("anhaenge") or []
    absender_name = (payload.get("absender_name") or "").strip()
    absender_email = (payload.get("absender_email") or "").strip()

    anfrageart = klassifiziere_anfrageart(text)
    ort, im_gebiet = erkenne_ort(text)

    ctx = {
        "text": text,
        "text_lower": text_lower,
        "anhaenge": anhaenge,
        "absender_name": absender_name,
        "telefon": (payload.get("telefon") or "").strip(),
        "ort": ort,
    }

    vorhandene: list[dict] = []
    fehlende: list[str] = []
    fragen: list[str] = []
    unsicherheiten: list[str] = []

    if anfrageart in branchen.ANFRAGEARTEN:
        felder = branchen.ANFRAGEARTEN[anfrageart]["pflichtfelder"]
        checkliste = branchen.ANFRAGEARTEN[anfrageart]["checkliste"]
    else:
        felder = []
        checkliste = ["Anfrageart telefonisch oder per Rückfrage klären"]
        unsicherheiten.append("Anfrageart konnte nicht sicher erkannt werden.")
        fragen.append("eine kurze Beschreibung, welche Leistung Sie benötigen")
        fehlende.append("Konkrete Leistungsbeschreibung")

    for feld in felder:
        wert = DETEKTOREN[feld["key"]](ctx)
        if wert:
            vorhandene.append({"feld": feld["label"], "wert": str(wert)})
        else:
            fehlende.append(feld["label"])
            fragen.append(feld["frage"])

    if ort and not im_gebiet:
        unsicherheiten.append(
            f"Ort „{ort}“ liegt möglicherweise außerhalb des Einzugsgebiets ({branchen.BETRIEB['region']})."
        )
    if not ort:
        unsicherheiten.append("Kein Objektort erkannt.")

    prioritaet, prio_begruendung = bestimme_prioritaet(
        anfrageart, text_lower, ort, im_gebiet, absender_email, absender_name
    )

    art_label = branchen.anfrageart_label(anfrageart)
    kontakt_teile = [t for t in (absender_name, absender_email, ctx["telefon"]) if t]
    kontakt = ", ".join(kontakt_teile) or "unbekannt"

    zusammenfassung = (
        f"{'Privat-/Kundenanfrage' if prioritaet != 'A' else 'Dringliche Anfrage'} "
        f"({payload.get('kanal', 'formular')}) zu „{art_label}“"
        + (f" in {ort}" if ort else ", Objektort unbekannt")
        + f". {len(vorhandene)} von {len(felder) or '?'} Pflichtangaben vorhanden"
        + (f", {len(anhaenge)} Anhang/Anhänge" if anhaenge else "")
        + "."
    )

    if prioritaet == "A":
        naechster_schritt = "Sofort telefonisch kontaktieren, danach Rückfrageentwurf prüfen."
    elif fehlende:
        naechster_schritt = "Rückfrageentwurf prüfen und freigeben."
    else:
        naechster_schritt = "Angebotsvorbereitung starten, ggf. Vor-Ort-Termin klären."

    rueckfrage = baue_rueckfrage(absender_name, fragen) if fragen else ""

    briefing = baue_briefing({
        "zusammenfassung": zusammenfassung,
        "kontakt": kontakt,
        "ort": ort,
        "anfrageart_label": art_label,
        "prioritaet": prioritaet,
        "prio_begruendung": prio_begruendung,
        "vorhandene_angaben": vorhandene,
        "fehlende_angaben": fehlende,
        "unsicherheiten": unsicherheiten,
        "naechster_schritt": naechster_schritt,
        "checkliste": checkliste,
    })

    return {
        "gewerk": branchen.GEWERK,
        "anfrageart": anfrageart,
        "ort": ort or "",
        "objektadresse": _det_objektadresse(ctx) or "",
        "ansprechpartner": absender_name,
        "telefon": _det_telefon(ctx) or "",
        "dringlichkeit": prioritaet,
        "zusammenfassung": zusammenfassung,
        "vorhandene_angaben": vorhandene,
        "fehlende_angaben": fehlende,
        "unsichere_angaben": [],
        "unsicherheiten": unsicherheiten,
        "rueckfrage_entwurf": rueckfrage,
        "internes_briefing": briefing,
        "naechster_schritt": naechster_schritt,
    }
