import os
import requests
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from langchain_amvera import AmveraLLM
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

AMVERA_API_KEY = os.getenv("AMVERA_API_KEY")
AMVERA_MODEL = "gpt-4.1"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_API_URL = "https://api.render.com/v1/services"

# Инициализация Amvera LLM
llm = AmveraLLM(model=AMVERA_MODEL, api_token=AMVERA_API_KEY)

app = FastAPI()

# Отправка сообщения в Telegram
def send_message(chat_id: int, text: str):
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

# Создание нового инстанса на Render
async def create_new_instance():
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "type": "web_service",
        "name": "bot-copy",  # Render добавит уникальный суффикс
        "env": "python",
        "repo": "https://github.com/fresh21green/my-cource-rep",
        "branch": "main",
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "python bot.py",
        "region": "oregon"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(RENDER_API_URL, headers=headers, json=payload)
        if resp.status_code != 201:
            return {"error": resp.text}
        return resp.json()

# Webhook для Telegram
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, None)

    # обработка кнопки "🚀 Клонировать"
    if update.callback_query:
        if update.callback_query.data == "clone":
            result = await create_new_instance()
            chat_id = update.callback_query.message.chat.id
            send_message(chat_id, f"✅ Новый инстанс создан!\n\n{result}")
        return JSONResponse(content={"ok": True})

    # обработка сообщений
    if update.message and update.message.text:
        chat_id = update.message.chat.id
        user_text = update.message.text

        # команда /start
        if user_text == "/start":
            keyboard = [[InlineKeyboardButton("🚀 Клонировать", callback_data="clone")]]
            reply_markup = {"inline_keyboard": [[{"text": "🚀 Клонировать", "callback_data": "clone"}]]}
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": "Привет! Нажми кнопку, чтобы клонировать бота:",
                "reply_markup": reply_markup
            })
            return JSONResponse(content={"ok": True})

        # команда /clone
        if user_text == "/clone":
            result = await create_new_instance()
            send_message(chat_id, f"✅ Новый инстанс создан!\n\n{result}")
            return JSONResponse(content={"ok": True})

        # обработка текста через Amvera LLM
        resp = llm.invoke(user_text)
        reply_text = str(resp)

        send_message(chat_id, reply_text)

    return JSONResponse(content={"ok": True})
