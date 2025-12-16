from fastapi import FastAPI, Request
from telegram import handle_telegram
from jobs import notify_users

app = FastAPI()

@app.post("/telegram")
async def telegram_webhook(req: Request):
    return await handle_telegram(req)

@app.get("/run")
def run():
    jobs = fetch_jobs()
    notify_users(jobs)
    return {"status": "sent"}
