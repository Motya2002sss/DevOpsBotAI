import os
import requests
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_KEY = os.getenv("API_KEY", "change-me")

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN is empty. Put it into .env")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def api_headers():
    return {"X-API-Key": API_KEY}


@bot.message_handler(commands=["start", "help"])
def start(m):
    bot.reply_to(
        m,
        "Команды:\n"
        "/incident текст — создать инцидент\n"
        "/incidents — последние инциденты\n"
    )


@bot.message_handler(commands=["incident"])
def create_incident(m):
    text = m.text.split(" ", 1)
    if len(text) < 2 or not text[1].strip():
        bot.reply_to(m, "Пример: /incident nexus не стартует")
        return

    title = text[1].strip()
    payload = {"title": title, "severity": "warn"}

    r = requests.post(f"{API_BASE_URL}/incidents", json=payload, headers=api_headers(), timeout=10)
    if r.status_code >= 300:
        bot.reply_to(m, f"Ошибка API: {r.status_code}\n{r.text}")
        return

    inc = r.json()
    bot.reply_to(
        m,
        f"✅ Создан инцидент\n"
        f"<b>{inc['title']}</b>\n"
        f"ID: <code>{inc['id']}</code>\n"
        f"Severity: {inc['severity']}, Status: {inc['status']}"
    )


@bot.message_handler(commands=["incidents"])
def list_incidents(m):
    r = requests.get(f"{API_BASE_URL}/incidents?limit=5", headers=api_headers(), timeout=10)
    if r.status_code >= 300:
        bot.reply_to(m, f"Ошибка API: {r.status_code}\n{r.text}")
        return

    items = r.json()
    if not items:
        bot.reply_to(m, "Пока нет инцидентов.")
        return

    lines = []
    for inc in items:
        lines.append(
            f"• <b>{inc['title']}</b>\n"
            f"  <code>{inc['id']}</code> | {inc['severity']} | {inc['status']}"
        )
    bot.reply_to(m, "\n\n".join(lines))


bot.infinity_polling(timeout=30, long_polling_timeout=30)

