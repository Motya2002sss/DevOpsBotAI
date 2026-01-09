from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Incident, Signal


def create_incident(db: Session, title: str, severity: str = "info", service: str | None = None, environment: str | None = None) -> Incident:
    inc = Incident(title=title, severity=severity, service=service, environment=environment)
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


def list_incidents(db: Session, limit: int = 20) -> list[Incident]:
    stmt = select(Incident).order_by(Incident.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_incident(db: Session, incident_id: UUID) -> Incident | None:
    return db.get(Incident, incident_id)


def add_signal(db: Session, incident_id: UUID, type_: str, source: str, payload: dict) -> Signal:
    sig = Signal(incident_id=incident_id, type=type_, source=source, payload=payload)
    db.add(sig)
    db.commit()
    db.refresh(sig)
    return sig


def list_signals(db: Session, incident_id: UUID, limit: int = 200) -> list[Signal]:
    stmt = (
        select(Signal)
        .where(Signal.incident_id == incident_id)
        .order_by(Signal.timestamp.asc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def find_recent_open_incident_by_title(db: Session, title: str, within_minutes: int = 30) -> Incident | None:
    since = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
    stmt = (
        select(Incident)
        .where(Incident.title == title)
        .where(Incident.status == "open")
        .where(Incident.created_at >= since)
        .order_by(Incident.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()

