import uuid
import requests

from app.db import SessionLocal
from app.crud import add_signal
from app.settings import settings


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

def notify_telegram(text: str) -> None:
    """
    Отправляет сообщение в Telegram в чат NOTIFY_CHAT_ID.
    Использует BOT_TOKEN (тот же токен, что у бота).
    """
    if not settings.bot_token or not settings.notify_chat_id:
        # ничего не делаем, если не настроено
        return

    url = f"https://api.telegram.org/bot{settings.bot_token}/sendMessage"
    payload = {
        "chat_id": settings.notify_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()

