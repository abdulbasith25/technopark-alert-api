from fastapi import FastAPI
import requests
import json
from sentence_transformers import SentenceTransformer, util

app = FastAPI()

# --------------------------
# CONFIG
# --------------------------
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

API_URL = "https://technopark.in/api/paginated-jobs?page=1&search=&type="
SEEN_FILE = "seen.json"

# Load seen jobs
try:
    with open(SEEN_FILE, "r") as f:
        seen = set(json.load(f))
except:
    seen = set()

# Telegram notifier
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# Load ML model
model = SentenceTransformer("Supabase/gte-tiny")
labels = [
    "fresher entry level 0-1 years junior",
    "experienced senior 3+ years"
]
label_emb = model.encode(labels, convert_to_tensor=True)

def classify(text):
    emb = model.encode(text, convert_to_tensor=True)
    sim = util.cos_sim(emb, label_emb)[0]
    return "fresher" if sim[0] > sim[1] else "experienced"

# --------------------------
# MAIN ENDPOINT
# --------------------------
@app.get("/run")
def run():
    global seen

    res = requests.get(API_URL)
    data = res.json().get("data", [])

    new_jobs = 0

    for job in data:
        job_id = job["id"]

        if job_id in seen:
            continue

        title = job["job_title"]
        desc = job["description"] or ""

        combined = f"{title} {desc}"

        result = classify(combined)

        if result == "fresher":
            new_jobs += 1
            msg = (
                f"🔥 NEW FRESHER JOB!\n"
                f"{title}\n"
                f"Company: {job['company']['company']}\n"
                f"Closing: {job['closing_date']}\n"
                f"Link: https://technopark.in/job/{job_id}"
            )
            send_telegram(msg)

        seen.add(job_id)

    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

    return {"status": "done", "new_fresher_jobs": new_jobs}
