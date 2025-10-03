import os
import requests
import httpx
from fastapi import FastAPI, Request
from telegram import  Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


#Подключаем Amvera адаптер
from langchain_amvera import AmveraLLM
from dotenv import load_dotenv

load_dotenv()

# LAOZHANG_API_KEY = os.getenv("LAOZHANG_API_KEY")
# LAOZHANG_MODEL = "gpt-4o"
# LAOZHANG_API_URL = "https://api.laozhang.ai/v1/chat/completions"

AMVERA_API_KEY = os.getenv("AMVERA_API_KEY")
AMVERA_MODEL = "gpt-4.1"
# AMVERA_API_URL = "https://models/gpt"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_API_URL = "https://api.render.com/v1/services"

# Поддерживаемые модели: llama8b, llama70b, gpt-4.1, gpt-5
llm = AmveraLLM(model="gpt-4.1", api_token=AMVERA_API_KEY)

app = FastAPI()

def send_message(chat_id: int, text: str):
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

# функция создания нового инстанса на Render
async def create_new_instance():
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "type": "web_service",
        "name": "bot-copy",  # Render сам добавит уникальный суффикс
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

# команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    keyboard = [
        [InlineKeyboardButton("🚀 Клонировать", callback_data="clone")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Нажми кнопку, чтобы клонировать бота:", reply_markup=reply_markup)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, None)

    # обработка кнопки /start
    if update.message.text == "/start":
        chat_id = update.message.chat.id
        keyboard = [[InlineKeyboardButton("🚀 Клонировать", callback_data="clone")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        send_message(chat_id, "Привет! Нажми кнопку, чтобы клонировать бота:")
        return {"ok": True}

    # обработка кнопки clone
    if update.callback_query:
        if update.callback_query.data == "clone":
            result = await create_new_instance()
            chat_id = update.callback_query.message.chat.id
            send_message(chat_id, f"✅ Новый инстанс создан!\n\n{result}")
        return {"ok": True}

    # обработка команд clone
    if update.message and update.message.text:
        if update.message.text == "/clone":
            result = await create_new_instance()
            send_message(update.message.chat.id, f"✅ Новый инстанс создан!\n\n{result}")
            return {"ok": True}

        user_text = update.message.text
        chat_id = update.message.chat.id 

        resp = llm.invoke(user_text)
        reply_text = str(resp)  # на всякий случай

        send_message(chat_id, reply_text)
        # Запрос в laozhang.ai
        # headers = {
        #     "Authorization": f"Bearer {LAOZHANG_API_KEY}",#LAOZHANG_API_KEY
        #     "Content-Type": "application/json"
        # }
        # payload = {
        #     "model": LAOZHANG_MODEL,#LAOZHANG_MODEL
        #     "messages": [
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": user_text}
        #     ]
        # }

        # try:
        #     resp = requests.post(LAOZHANG_API_URL, headers=headers, json=payload),#LAOZHANG_API_URL
        #     if resp.status_code == 200:
        #         data = resp.json()
        #         reply_text = data["choices"][0]["message"]["content"]
        #     else:
        #         reply_text = f"Ошибка API: {resp.text}"
        # except Exception as e:
        #     reply_text = f"Ошибка запроса: {e}"

        # Запрос в amvera

    return {"ok": True}
