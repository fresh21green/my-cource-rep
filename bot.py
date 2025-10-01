import os
import requests
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- Переменные окружения ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
LAOZHANG_API_KEY = os.getenv("LAOZHANG_API_KEY")
LAOZHANG_API_URL = "https://api.laozhang.ai/v1/chat/completions"
LAOZHANG_MODEL = "gpt-4o"

# --- FastAPI app ---
app = FastAPI()

# --- Telegram Application ---
application = Application.builder().token(TELEGRAM_TOKEN).build()

# --- Handlers ---
async def start(update: Update, context):
    await update.message.reply_text("Привет 👋! Я бот, работаю через laozhang.ai 🚀")

async def chat(update: Update, context):
    user_text = update.message.text

    headers = {
        "Authorization": f"Bearer {LAOZHANG_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": LAOZHANG_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_text}
        ]
    }

    try:
        resp = requests.post(LAOZHANG_API_URL, headers=headers, json=payload)
        if resp.status_code == 200:
            data = resp.json()
            reply_text = data["choices"][0]["message"]["content"]
        else:
            reply_text = f"Ошибка API: {resp.text}"
    except Exception as e:
        reply_text = f"Ошибка запроса: {e}"

    await update.message.reply_text(reply_text)

# Регистрируем handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

# --- Webhook endpoint ---
@app.on_event("startup")
async def startup_event():
    """Инициализируем бота при старте FastAPI"""
    await application.initialize()
    await application.start()

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
