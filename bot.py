import os
import requests
import re
import base64
from fastapi import FastAPI, Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

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

# Поддерживаемые модели: llama8b, llama70b, gpt-4.1, gpt-5
llm = AmveraLLM(model="gpt-4.1", api_token=AMVERA_API_KEY)

app = FastAPI()


def send_message(chat_id: int, text: str, parse_mode="Markdown", reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json=payload)

def send_photo(chat_id: int, photo_url: str, caption=None):
    payload = {
        "chat_id": chat_id,
        "photo": photo_url
    }
    if caption:
        payload["caption"] = caption
    requests.post(f"{TELEGRAM_API_URL}/sendPhoto", json=payload)

def send_photo_file(chat_id: int, image_bytes: bytes, caption=None):
    files = {"photo": ("image.png", image_bytes)}
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    requests.post(f"{TELEGRAM_API_URL}/sendPhoto", data=data, files=files)


def process_llm_response(chat_id: int, response: str):
    """
    Обработка ответа нейросети:
    - Отправляем всё по порядку (текст, код, картинки).
    """

    # Регулярка: ищем либо блок кода, либо ссылку на картинку
    pattern = re.compile(
        r"```(.*?)```|(https?://[^\s]+\.(?:png|jpg|jpeg|gif))|(data:image[^\s]+)",
        re.DOTALL
    )

    last_end = 0
    for match in pattern.finditer(response):
        start, end = match.span()

        # 1. Текст до спец-блока
        if start > last_end:
            text_chunk = response[last_end:start].strip()
            if text_chunk:
                send_message(chat_id, text_chunk)

        # 2. Код
        if match.group(1):
            block = match.group(1)
            if "\n" in block:
                lang, code = block.split("\n", 1)
            else:
                lang, code = "text", block
            formatted_code = f"```{lang}\n{code.strip()}\n```"
            send_message(chat_id, formatted_code, parse_mode="Markdown")

        # 3. Ссылка на картинку
        elif match.group(2):
            url = match.group(2)
            send_photo(chat_id, url, caption="🖼 Картинка")

        # 4. Base64 картинка
        elif match.group(3):
            try:
                header, encoded = match.group(3).split(",", 1)
                image_bytes = base64.b64decode(encoded)
                send_photo_file(chat_id, image_bytes, caption="🖼 Сгенерированное изображение")
            except Exception as e:
                send_message(chat_id, f"⚠️ Ошибка обработки base64: {e}")

        last_end = end

    # 5. Оставшийся текст после последнего блока
    if last_end < len(response):
        tail = response[last_end:].strip()
        if tail:
            send_message(chat_id, tail)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, None)

    if update.message and update.message.text:
        user_text = update.message.text
        chat_id = update.message.chat.id
        
        # Ответ через Amvera LLM
        resp = llm.invoke(user_text)
        reply_text = resp.content if hasattr(resp, "content") else str(resp)

        process_llm_response(chat_id, reply_text)

    return {"ok": True}
