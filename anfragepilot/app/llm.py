"""LLM-Analyse über die Anthropic Messages API mit strukturiertem JSON-Output.

Die Analyse liefert exakt die Struktur, die auch app.rules.analyse() erzeugt.
Schlägt der Aufruf fehl (kein Key, Netzwerk, Refusal), fällt die Pipeline auf
die regelbasierte Analyse zurück – der KI-Ausfall blockiert nie den Eingang.
"""

from __future__ import annotations

import json
import os

from . import branchen

MODEL = os.environ.get("ANFRAGEPILOT_MODEL", "claude-opus-4-8")
PROMPT_VERSION = "v1"

_ANGABE_SCHEMA = {
    "type": "object",
    "properties": {
        "feld": {"type": "string"},
        "wert": {"type": "string"},
    },
    "required": ["feld", "wert"],
    "additionalProperties": False,
}

ANALYSE_SCHEMA = {
    "type": "object",
    "properties": {
        "gewerk": {"type": "string"},
        "anfrageart": {
            "type": "string",
            "enum": list(branchen.ANFRAGEARTEN.keys()) + [branchen.ANFRAGEART_UNKLAR],
        },
        "ort": {"type": "string"},
        "objektadresse": {"type": "string"},
        "ansprechpartner": {"type": "string"},
        "telefon": {"type": "string"},
        "dringlichkeit": {"type": "string", "enum": branchen.PRIORITAETEN},
        "zusammenfassung": {"type": "string"},
        "vorhandene_angaben": {"type": "array", "items": _ANGABE_SCHEMA},
        "fehlende_angaben": {"type": "array", "items": {"type": "string"}},
        "unsichere_angaben": {"type": "array", "items": {"type": "string"}},
        "unsicherheiten": {"type": "array", "items": {"type": "string"}},
        "rueckfrage_entwurf": {"type": "string"},
        "internes_briefing": {"type": "string"},
        "naechster_schritt": {"type": "string"},
    },
    "required": [
        "gewerk", "anfrageart", "ort", "objektadresse", "ansprechpartner",
        "telefon", "dringlichkeit", "zusammenfassung", "vorhandene_angaben",
        "fehlende_angaben", "unsichere_angaben", "unsicherheiten",
        "rueckfrage_entwurf", "internes_briefing", "naechster_schritt",
    ],
    "additionalProperties": False,
}


def _pflichtfeld_katalog() -> str:
    zeilen = []
    for key, art in branchen.ANFRAGEARTEN.items():
        zeilen.append(f"\n### Anfrageart „{art['label']}“ (key: {key})")
        zeilen.append("Pflichtfelder:")
        for feld in art["pflichtfelder"]:
            zeilen.append(f"- {feld['label']}")
        zeilen.append("Interne Checkliste:")
        for punkt in art["checkliste"]:
            zeilen.append(f"- {punkt}")
    return "\n".join(zeilen)


def system_prompt() -> str:
    orte = ", ".join(branchen.EINZUGSGEBIET)
    return f"""Du bist der Anfrage-Analyse-Assistent von „{branchen.BETRIEB['name']}“,
einem {branchen.GEWERK}-Betrieb im Raum {branchen.BETRIEB['region']}.
Du analysierst eingehende Kundenanfragen (E-Mail oder Kontaktformular) und
bereitest sie für das Büro auf. Du triffst keine Entscheidungen nach außen –
jeder Entwurf wird von einem Menschen geprüft und freigegeben.

Einzugsgebiet: {orte}. Liegt der Objektort erkennbar außerhalb, vergib
Dringlichkeit "C" und vermerke das unter "unsicherheiten".

Anfragearten und Pflichtfelder:
{_pflichtfeld_katalog()}

Aufgaben:
1. Anfrageart erkennen (einer der Keys oder "unklar").
2. Kundendaten, Objektadresse und Ort extrahieren – nur was wirklich im Text steht.
3. Pflichtfelder der erkannten Anfrageart prüfen: vorhandene Angaben mit Wert
   auflisten ("vorhandene_angaben"), fehlende als Feldnamen ("fehlende_angaben"),
   unsichere/mehrdeutige unter "unsichere_angaben".
4. Dringlichkeit A/B/C: A = Notdienst, hoher Wert, B2B oder klarer Zeitdruck;
   B = normal bearbeitbar; C = unklar, unvollständig, geringe Passung oder
   außerhalb des Einzugsgebiets.
5. Kurze interne Zusammenfassung (1–2 Sätze, sachlich).
6. Rückfrageentwurf ("rueckfrage_entwurf"): freundliche, kurze E-Mail
   (maximal ca. 140 Wörter), die NUR tatsächlich fehlende Angaben erfragt.
   Verbindliche Regeln: keine Preisangaben oder Preiszusagen, keine
   Terminzusagen, keine technischen Diagnosen, nichts erfinden.
   Signatur als Platzhalter "[Betrieb]". Wenn nichts fehlt: leerer String.
7. Internes Angebots-Briefing ("internes_briefing"): Zusammenfassung,
   Kontakt, Objekt/Ort, Anfrageart, Priorität mit Begründung, bekannte und
   fehlende Angaben, Risiken/Unsicherheiten, empfohlener nächster Schritt und
   die interne Checkliste der Anfrageart (als Text mit Zeilenumbrüchen).
8. "naechster_schritt": eine konkrete Empfehlung für das Büro.

Erfinde niemals Angaben, die nicht in der Anfrage stehen. Unsicherheiten
immer explizit ausweisen."""


def llm_verfuegbar() -> bool:
    modus = os.environ.get("ANFRAGEPILOT_USE_LLM", "auto").lower()
    if modus == "off":
        return False
    if modus == "on":
        return True
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


def _user_prompt(payload: dict) -> str:
    anhaenge = payload.get("anhaenge") or []
    return (
        f"Eingangskanal: {payload.get('kanal', 'formular')}\n"
        f"Absender: {payload.get('absender_name') or 'unbekannt'}"
        f" <{payload.get('absender_email') or 'unbekannt'}>\n"
        f"Telefon (Formularfeld): {payload.get('telefon') or '-'}\n"
        f"Betreff: {payload.get('betreff') or '-'}\n"
        f"Anhänge: {', '.join(anhaenge) if anhaenge else 'keine'}\n\n"
        f"Nachricht:\n{payload.get('nachricht', '')}"
    )


def analyse(payload: dict) -> dict:
    """Analysiert eine Anfrage per Claude. Wirft bei jedem Fehler eine Exception –
    der Aufrufer entscheidet über den Fallback."""
    import anthropic  # lazy: App bleibt ohne installiertes SDK lauffähig (Fallback)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=system_prompt(),
        messages=[{"role": "user", "content": _user_prompt(payload)}],
        output_config={"format": {"type": "json_schema", "schema": ANALYSE_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("LLM-Analyse abgelehnt (stop_reason=refusal)")
    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        raise RuntimeError("LLM-Antwort enthielt keinen Textblock")
    daten = json.loads(text)
    return _normalisiere(daten)


def _normalisiere(daten: dict) -> dict:
    """Guardrails auf LLM-Output: Enums erzwingen, Listen absichern."""
    if daten.get("anfrageart") not in list(branchen.ANFRAGEARTEN) + [branchen.ANFRAGEART_UNKLAR]:
        daten["anfrageart"] = branchen.ANFRAGEART_UNKLAR
    if daten.get("dringlichkeit") not in branchen.PRIORITAETEN:
        daten["dringlichkeit"] = "B"
    for liste in ("vorhandene_angaben", "fehlende_angaben", "unsichere_angaben", "unsicherheiten"):
        if not isinstance(daten.get(liste), list):
            daten[liste] = []
    for feld in ("gewerk", "ort", "objektadresse", "ansprechpartner", "telefon",
                 "zusammenfassung", "rueckfrage_entwurf", "internes_briefing",
                 "naechster_schritt"):
        if not isinstance(daten.get(feld), str):
            daten[feld] = ""
    return daten
