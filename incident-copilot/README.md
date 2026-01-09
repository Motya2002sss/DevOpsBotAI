# Incident Copilot (MVP)

Запуск:
1) `cp .env.example .env`
2) Заполни `BOT_TOKEN` и поменяй `API_KEY`
3) `docker compose up --build`

Проверка:
- `curl http://localhost:8000/health`
- в Telegram: `/start`, `/incident ...`, `/incidents`

Webhook (пример):
- `POST http://localhost:8000/webhooks/alert`
- (если задан WEBHOOK_TOKEN) добавь header `X-Webhook-Token: <token>`

