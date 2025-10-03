import os
import requests
from fastapi import FastAPI, Request
from telegram import Update

#Подключаем Amvera адаптер
from langchain_amvera import AmveraLLM
from dotenv import load_dotenv

load_dotenv()

# LAOZHANG_API_KEY = os.getenv("LAOZHANG_API_KEY")
# LAOZHANG_MODEL = "gpt-4o"
# LAOZHANG_API_URL = "https://api.laozhang.ai/v1/chat/completions"

AMVERA_API_KEY = os.getenv("AMVERA_API_KEY")
AMVERA_MODEL = "gpt-4.1"
AMVERA_API_URL = "https://models/gpt"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Поддерживаемые модели: llama8b, llama70b, gpt-4.1, gpt-5
llm = AmveraLLM(model="gpt-4.1", api_token=AMVERA_API_KEY)

app = FastAPI()

def send_message(chat_id: int, text: str):
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, None)

    if update.message and update.message.text:
        user_text = update.message.text
        chat_id = update.message.chat.id
        resp = llm.invoke(user_text)
        reply_text = str(resp)  # resp.content

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
