import os
import requests
from datetime import datetime
from fastapi import Request
from storage import add_user

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text})

async def handle_telegram(req: Request):
    payload = await req.json()
    message = payload.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))
    text = message.get("text", "")

    if text == "/start":
        add_user(chat_id, datetime.utcnow().isoformat())
        send_telegram(chat_id, "✅ Job alerts activated")

    return {"status": "ok"}
