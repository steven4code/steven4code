"""AnfragePilot Handwerk – MVP-Webanwendung.

Start:  uvicorn app.main:app --reload  (im Ordner anfragepilot/)
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from . import branchen, llm, reporting, service

app = FastAPI(title="AnfragePilot Handwerk", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.globals.update(
    branchen=branchen,
    betrieb=branchen.BETRIEB,
    statuswerte=branchen.STATUSWERTE,
)


def _mailto(fall: dict) -> str:
    betreff = f"Re: {fall['betreff']}" if fall["betreff"] else "Ihre Anfrage"
    return (
        f"mailto:{fall['absender_email']}?subject={quote(betreff)}"
        f"&body={quote(fall['rueckfrage_entwurf'])}"
    )


# ---------------------------------------------------------------- Dashboard

@app.get("/")
def dashboard(request: Request, status: str = "", prioritaet: str = "", freigabe: str = ""):
    faelle = service.faelle_auflisten(status=status, prioritaet=prioritaet, freigabe=freigabe)
    return templates.TemplateResponse(request, "dashboard.html", {
        "faelle": faelle,
        "kpi": service.kennzahlen(),
        "filter_status": status,
        "filter_prioritaet": prioritaet,
        "filter_freigabe": freigabe,
        "llm_aktiv": llm.llm_verfuegbar(),
        "llm_model": llm.MODEL,
    })


@app.get("/fall/{fall_id}")
def fall_detail(request: Request, fall_id: str):
    try:
        fall = service.fall_holen(fall_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Fall nicht gefunden")
    return templates.TemplateResponse(request, "fall_detail.html", {
        "fall": fall,
        "audit": service.audit_fuer_fall(fall_id),
        "ai_outputs": service.ai_outputs_fuer_fall(fall_id),
        "mailto": _mailto(fall),
    })


# ------------------------------------------------------- Aktionen (Freigabe)

@app.post("/fall/{fall_id}/entwurf")
def entwurf_speichern(fall_id: str, entwurf: str = Form(""), actor: str = Form("büro")):
    service.entwurf_speichern(fall_id, entwurf, actor=actor)
    return RedirectResponse(url=f"/fall/{fall_id}", status_code=303)


@app.post("/fall/{fall_id}/freigabe")
def freigabe(fall_id: str, aktion: str = Form(...), kommentar: str = Form(""),
             actor: str = Form("büro")):
    if aktion == "freigeben":
        service.entwurf_freigeben(fall_id, actor=actor)
    elif aktion == "ablehnen":
        service.entwurf_ablehnen(fall_id, kommentar=kommentar, actor=actor)
    else:
        raise HTTPException(status_code=400, detail="Unbekannte Aktion")
    return RedirectResponse(url=f"/fall/{fall_id}", status_code=303)


@app.post("/fall/{fall_id}/status")
def status_aendern(fall_id: str, status: str = Form(...), actor: str = Form("büro")):
    try:
        service.status_setzen(fall_id, status, actor=actor)
    except service.Eingabefehler as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse(url=f"/fall/{fall_id}", status_code=303)


@app.post("/fall/{fall_id}/verantwortlicher")
def verantwortlicher(fall_id: str, name: str = Form("")):
    service.verantwortlichen_setzen(fall_id, name)
    return RedirectResponse(url=f"/fall/{fall_id}", status_code=303)


# ------------------------------------------------------------------- Intake

@app.get("/neu")
def intake_formular(request: Request):
    return templates.TemplateResponse(request, "intake.html", {})


@app.post("/neu")
def intake_absenden(
    kanal: str = Form("formular"),
    absender_name: str = Form(""),
    absender_email: str = Form(""),
    telefon: str = Form(""),
    betreff: str = Form(""),
    nachricht: str = Form(...),
    anhaenge: str = Form(""),
):
    try:
        fall = service.eingang_verarbeiten({
            "kanal": kanal,
            "absender_name": absender_name,
            "absender_email": absender_email,
            "telefon": telefon,
            "betreff": betreff,
            "nachricht": nachricht,
            "anhaenge": anhaenge,
        })
    except service.Eingabefehler as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return RedirectResponse(url=f"/fall/{fall['fall_id']}", status_code=303)


class AnfrageEingang(BaseModel):
    """Webhook-Payload für Formular-/E-Mail-Anbindung (z. B. n8n, Make, Tally)."""
    kanal: str = Field(default="formular", pattern="^(email|formular)$")
    absender_name: str = ""
    absender_email: str = ""
    telefon: str = ""
    betreff: str = ""
    nachricht: str
    anhaenge: list[str] = []


@app.post("/api/anfragen", status_code=201)
def api_anfrage(eingang: AnfrageEingang):
    try:
        fall = service.eingang_verarbeiten(eingang.model_dump())
    except service.Eingabefehler as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "fall_id": fall["fall_id"],
        "status": fall["status"],
        "prioritaet": fall["prioritaet"],
        "anfrageart": fall["anfrageart"],
        "fehlende_angaben": fall["fehlende_angaben"],
        "freigabe_status": fall["freigabe_status"],
    }


@app.get("/api/anfragen/{fall_id}")
def api_fall(fall_id: str):
    try:
        return service.fall_holen(fall_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Fall nicht gefunden")


# ------------------------------------------------------------------- Report

@app.get("/report")
def report(request: Request, monat: str = ""):
    daten = reporting.monatsreport(monat)
    return templates.TemplateResponse(request, "report.html", {
        "report": daten,
        "monate": reporting.verfuegbare_monate(),
    })
