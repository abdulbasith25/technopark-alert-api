from fastapi import FastAPI
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer

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

# --------- SIMPLE CLASSIFIER ----------
KEYWORDS = [
    "fresher", "entry level", "0-1", "0-2",
    "junior", "trainee", "graduate", "beginner"
]

vectorizer = TfidfVectorizer(stop_words="english")

train_x = [
    "fresher entry level opportunity 0-1 year experience",
    "junior developer trainee role",
    "experience minimum 3 years senior developer",
    "looking for experienced candidate 5 years"
]
train_y = [1, 1, 0, 0]

vectorizer.fit(train_x)

def classify(text):
    text_low = text.lower()

    # keyword check
    for k in KEYWORDS:
        if k in text_low:
            return "fresher"

    # fallback
    score = vectorizer.transform([text_low]).toarray().sum()
    return "fresher" if score > 0.1 else "experienced"


@app.get("/run")
def run():
    # send_telegram("🔥 /run executed successfully")

    global seen

    # --- STATIC TEST JOB ---
    test_job_id = -1
    if test_job_id not in seen:
        send_telegram("🔔 CRON TEST: The script is running successfully!")
        seen.add(test_job_id)

    res = requests.get(API_URL)
    data = res.json().get("data", [])

    new_jobs = 0

    for job in data:
        job_id = job["id"]
        if job_id in seen:
            continue

        title = job.get("job_title", "")
        short_desc = job.get("short_description", "")

        combined = f"{title} {short_desc}"

        if classify(combined) == "fresher":
            new_jobs += 1

            msg = (
                f"🔥 NEW FRESHER JOB!\n"
                f"{title}\n"
                f"Company: {job.get('company', {}).get('company', 'N/A')}\n"
                f"Closing: {job.get('closing_date', 'N/A')}\n"
                f"Link: https://technopark.in/job-details/{job_id}"
            )

            send_telegram(msg)

        seen.add(job_id)

    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

    return {"status": "ok", "new_fresher_jobs": new_jobs}
