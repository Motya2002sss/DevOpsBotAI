import uuid

from app.db import SessionLocal
from app.crud import add_signal


def enrich_incident(incident_id: str) -> None:
    # Заготовка: позже добавим TeamCity/Nexus/logs enrichment
    inc_uuid = uuid.UUID(incident_id)

    db = SessionLocal()
    try:
        add_signal(
            db,
            incident_id=inc_uuid,
            type_="enrich",
            source="worker",
            payload={"message": "enrichment finished (stub)", "next": ["teamcity", "nexus", "logs"]},
        )
    finally:
        db.close()

