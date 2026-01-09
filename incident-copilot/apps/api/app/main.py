import uuid
from typing import Annotated

from fastapi import FastAPI, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.settings import settings
from app import crud
from app.schemas import IncidentCreate, IncidentOut, SignalOut
from app.queue import incident_queue
from app.tasks import enrich_incident

app = FastAPI(title="Incident Copilot")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_api_key(x_api_key: Annotated[str | None, Header()] = None):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def require_webhook_token(x_webhook_token: Annotated[str | None, Header()] = None):
    # Если WEBHOOK_TOKEN не задан — пропускаем
    if not settings.webhook_token:
        return
    if x_webhook_token != settings.webhook_token:
        raise HTTPException(status_code=401, detail="Invalid webhook token")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/incidents", response_model=IncidentOut, dependencies=[Depends(require_api_key)])
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    inc = crud.create_incident(
        db,
        title=payload.title,
        severity=payload.severity,
        service=payload.service,
        environment=payload.environment,
    )
    crud.add_signal(db, inc.id, "manual", "api", {"title": payload.title})

    incident_queue.enqueue(enrich_incident, str(inc.id))
    return inc


@app.get("/incidents", response_model=list[IncidentOut], dependencies=[Depends(require_api_key)])
def list_incidents(limit: int = 20, db: Session = Depends(get_db)):
    return crud.list_incidents(db, limit=limit)


@app.get("/incidents/{incident_id}", response_model=IncidentOut, dependencies=[Depends(require_api_key)])
def get_incident(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    inc = crud.get_incident(db, incident_id)
    if not inc:
        raise HTTPException(404, "Incident not found")
    return inc


@app.get("/incidents/{incident_id}/signals", response_model=list[SignalOut], dependencies=[Depends(require_api_key)])
def get_signals(incident_id: uuid.UUID, db: Session = Depends(get_db)):
    return crud.list_signals(db, incident_id)


@app.post("/webhooks/alert")
async def webhook_alert(request: Request, db: Session = Depends(get_db), _: None = Depends(require_webhook_token)):
    """
    Упрощённый вход:
    - Если пришёл Alertmanager payload: берём alerts[0].labels.alertname / service
    - Иначе ждём { "title": "...", "severity": "warn" }
    """
    body = await request.json()

    title = None
    severity = "warn"
    service = None
    environment = None

    if isinstance(body, dict) and "alerts" in body and body["alerts"]:
        a0 = body["alerts"][0]
        labels = a0.get("labels", {}) or {}
        annotations = a0.get("annotations", {}) or {}
        title = labels.get("alertname") or annotations.get("summary") or "Alert"
        severity = labels.get("severity") or severity
        service = labels.get("service") or labels.get("job")
        environment = labels.get("env") or labels.get("environment")
    else:
        title = body.get("title") if isinstance(body, dict) else "Alert"
        severity = (body.get("severity") if isinstance(body, dict) else None) or severity

    existing = crud.find_recent_open_incident_by_title(db, title, within_minutes=30)
    if existing:
        inc = existing
    else:
        inc = crud.create_incident(db, title=title, severity=severity, service=service, environment=environment)

    crud.add_signal(db, inc.id, "alert", "webhook", body)
    incident_queue.enqueue(enrich_incident, str(inc.id))
    return {"ok": True, "incident_id": str(inc.id), "reused": bool(existing)}

