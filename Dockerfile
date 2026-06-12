FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Menjalankan bot
CMD ["python", "bot.py"]

LABEL maintainer="Telegram-Sheet-Bot"