FROM python:3.9-slim

WORKDIR /app

# Установим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем код
COPY . .

# Запуск FastAPI через uvicorn
CMD ["uvicorn", "bot:app", "--host", "0.0.0.0", "--port", "7860"]