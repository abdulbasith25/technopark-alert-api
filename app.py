from fastapi import FastAPI, HTTPException
import requests
import json
import os
from datetime import datetime

# -----------------------------------
# IMPORT GEMINI
# -----------------------------------
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI"))

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for testing; tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------
# TELEGRAM SETTINGS
# -----------------------------------
TELEGRAM_TOKEN = "8032200545:AAEMFO914zack8tWDhG5XfRftfH9fP-qBMM"
CHAT_ID = "727552569"

def send_telegram(msg: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# -----------------------------------
# STORAGE FILES
# -----------------------------------
SEEN_FILE = "seen.json"
CV_FILE = "cv_text.json"
DAILY_FILE = "daily_sent.json"     # <---- NEW: Prevent spamming at 12 PM

# Load seen jobs
try:
    with open(SEEN_FILE, "r") as f:
        seen = set(json.load(f))
except:
    seen = set()

# Load stored CV
try:
    with open(CV_FILE, "r") as f:
        STORED_CV = json.load(f)
except:
    STORED_CV = {"cv_text": ""}

# Load last daily sent info
try:
    with open(DAILY_FILE, "r") as f:
        last_daily = json.load(f)
except:
    last_daily = {"date": ""}


# -----------------------------------
# API TO RECEIVE CV FROM REACT (POST)
# -----------------------------------
@app.post("/upload_cv")
def upload_cv(payload: dict):
    cv_text = payload.get("cv_text", "").strip()
    if not cv_text:
        raise HTTPException(400, "cv_text is empty")

    # Store the CV text
    with open(CV_FILE, "w") as f:
        json.dump({"cv_text": cv_text, "uploaded_at": str(datetime.utcnow())}, f)

    return {"status": "stored", "length": len(cv_text)}


# -----------------------------------
# FETCH JOBS FROM TECHNOPARK API
# -----------------------------------
API_URL = "https://technopark.in/api/paginated-jobs?page=1&search=&type="

def fetch_jobs():
    try:
        res = requests.get(API_URL, timeout=10)
        data = res.json().get("data", [])
        return data
    except:
        return []


# -----------------------------------
# GEMINI MATCHING FUNCTION
# -----------------------------------
def analyze_with_gemini(cv_text: str, jobs: list):
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are an AI job-matching assistant.

Candidate CV:
{cv_text}

Job Listings:
{json.dumps(jobs)}

TASK:
1. Pick the TOP 5 best-matching jobs.
2. Provide: job title, company, match score (0–100), short reason, and job link.

Return ONLY JSON in this exact format:
[
  {{
    "title": "",
    "company": "",
    "match_score": 0,
    "reason": "",
    "link": ""
  }}
]
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error contacting Gemini: {str(e)}"


# -----------------------------------
# CRON JOB ENDPOINT (Render pings this)
# Runs every 5 minutes
# -----------------------------------
@app.get("/run")
def run():
    global last_daily

    # Load the stored CV
    try:
        with open(CV_FILE, "r") as f:
            stored = json.load(f)
            cv_text = stored.get("cv_text", "")
    except:
        cv_text = ""

    if not cv_text.strip():
        send_telegram("⚠️ No CV uploaded yet — cannot run matching.")
        return {"status": "no_cv"}

    # Fetch latest jobs
    jobs = fetch_jobs()

    if not jobs:
        send_telegram("⚠️ No jobs found from API.")
        return {"status": "no_jobs"}

    # TIME CHECK (UTC OR LOCAL? Use UTC for safety)
    now = datetime.utcnow()
    today_date = now.strftime("%Y-%m-%d")

    # -----------------------------------
    # DAILY 12 PM SUMMARY — ONLY ONCE
    # -----------------------------------
    if now.hour == 12 and last_daily.get("date") != today_date:
        gemini_output = analyze_with_gemini(cv_text, jobs)
        msg = f"🌞 *Your Daily 12 PM Job Summary*\n\n{gemini_output}"
        send_telegram(msg)

        # Update last sent date
        last_daily["date"] = today_date
        with open(DAILY_FILE, "w") as f:
            json.dump(last_daily, f)

        return {"status": "daily_summary_sent"}

    # -----------------------------------
    # NORMAL 5-MINUTE JOB CHECK (NO SPAM)
    # -----------------------------------
    # gemini_output = analyze_with_gemini(cv_text, jobs)
    # msg = f"🔥 *Updated Job Matches Based on Your CV*\n\n{gemini_output}"
    # send_telegram(msg)

    return {"status": "success", "sent_to_telegram": True}
