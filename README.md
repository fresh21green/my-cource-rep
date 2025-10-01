---
title: My Telegram Bot Space
emoji: 🤖
colorFrom: pink
colorTo: indigo
sdk: fastapi
app_file: bot.py
pinned: false
license: mit
python_version: "3.9"
---



# 🤖 Telegram Bot + laozhang.ai на Hugging Face Spaces

Этот Space разворачивает Telegram-бота, который отвечает пользователю через API laozhang.ai.

## ⚙️ Настройка

1. В **Settings → Variables** добавь:
   - `TELEGRAM_BOT_TOKEN` = токен от BotFather
   - `LAOZHANG_API_KEY` = твой ключ laozhang.ai

2. В **Settings → App file** укажи `bot.py`.  
   Переменная в коде должна называться **app** (как у нас `app = FastAPI()`).

3. После деплоя Space будет доступен по URL:
https://<username>-<space-name>.hf.space



4. Зарегистрируй webhook в Telegram:
```bash
curl -F "url=https://<username>-<space-name>.hf.space/webhook" \
     https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook
