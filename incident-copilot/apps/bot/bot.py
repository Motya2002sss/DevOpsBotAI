import os
import requests
import telebot
import html

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
        "/chatid — показать chat_id (для уведомлений)\n"
        "/analyze id — AI-разбор инцидента\n"
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

@bot.message_handler(commands=["chatid"])
def chatid(m):
    bot.reply_to(m, f"chat_id: <code>{m.chat.id}</code>")
@bot.message_handler(commands=["chatid"])
def chatid(m):
    bot.reply_to(m, f"chat_id: <code>{m.chat.id}</code>")


@bot.message_handler(commands=["analyze"])
def analyze_cmd(m):
    try:
        parts = m.text.split(" ", 1)
        if len(parts) < 2 or not parts[1].strip():
            bot.reply_to(m, "Пример: /analyze incident_id")
            return

        incident_id = parts[1].strip()

        r = requests.post(
            f"{API_BASE_URL}/incidents/{incident_id}/analyze",
            headers=api_headers(),
            timeout=20
        )
        if r.status_code >= 300:
            bot.reply_to(m, f"Ошибка API: {r.status_code}\n{r.text}")
            return

        data = r.json()  # <-- ВАЖНО: data присваиваем ДО использования

        safe_title = html.escape(str(data.get("title", "")))
        safe_inc_id = html.escape(str(data.get("incident_id", "")))
        safe_tldr = html.escape(str(data.get("tldr", "")))

        hypotheses = data.get("hypotheses", []) or []
        next_steps = data.get("next_steps", []) or []
        questions = data.get("questions", []) or []

        hyp_lines = "\n".join([f"• {html.escape(str(h))}" for h in hypotheses]) or "—"
        step_lines = "\n".join([f"• <code>{html.escape(str(s))}</code>" for s in next_steps]) or "—"
        q_lines = "\n".join([f"• {html.escape(str(q))}" for q in questions]) or "—"

        text = (
            f"🤖 <b>AI анализ</b>\n"
            f"🧾 <b>Инцидент:</b> {safe_title}\n"
            f"ID: <code>{safe_inc_id}</code>\n\n"
            f"🧠 <b>TL;DR:</b> {safe_tldr}\n\n"
            f"🧩 <b>Гипотезы:</b>\n{hyp_lines}\n\n"
            f"🛠 <b>Следующие шаги:</b>\n{step_lines}\n\n"
            f"❓ <b>Вопросы:</b>\n{q_lines}"
        )

        bot.reply_to(m, text)

    except Exception as e:
        # чтобы бот не падал “в целом” из-за одной ошибки
        bot.reply_to(m, f"Ошибка в /analyze: {e}")

bot.infinity_polling(timeout=30, long_polling_timeout=30)
