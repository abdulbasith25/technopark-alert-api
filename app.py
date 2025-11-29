from fastapi import FastAPI
import requests
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

app = FastAPI()

TELEGRAM_TOKEN = "8032200545:AAEMFO914zack8tWDhG5XfRftfH9fP-qBMM"
CHAT_ID = "727552569"

API_URL = "https://technopark.in/api/paginated-jobs?page=1&search=&type="
SEEN_FILE = "seen.json"

# Load seen IDs
try:
    with open(SEEN_FILE, "r") as f:
        seen = set(json.load(f))
except:
    seen = set()

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# --------- LIGHTWEIGHT ML CLASSIFIER ----------
KEYWORDS = [
    "fresher", "entry level", "0-1 year", "0-2 years", "junior", "trainee",
    "graduate", "looking for beginners"
]

vectorizer = TfidfVectorizer(stop_words="english")

# small training samples
train_x = [
    "fresher entry level opportunity 0-1 year experience",
    "junior developer trainee role",
    "experience minimum 3 years senior developer",
    "looking for experienced candidate 5 years"
]
train_y = [1, 1, 0, 0]  # 1 = fresher, 0 = experienced

vectorizer.fit(train_x)

def classify(text):
    text_low = text.lower()

    # keyword score
    for k in KEYWORDS:
        if k in text_low:
            return "fresher"

    # tfidf fallback
    vec = vectorizer.transform([text_low])
    score = vec.toarray().sum()

    return "fresher" if score > 1 else "experienced"


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
        desc = job.get("description", "")

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

    return {"status": "ok", "new_fresher_jobs": new_jobs}
