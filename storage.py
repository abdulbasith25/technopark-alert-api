import json

USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

def get_user(chat_id):
    users = load_users()
    return users.get(chat_id)

def add_user(chat_id, joined_at):
    users = load_users()
    if chat_id not in users:
        users[chat_id] = {
            "joined_at": joined_at,
            "sent_jobs": []
        }
        save_users(users)

def add_sent_job(chat_id, job_id):
    users = load_users()
    if chat_id in users:
        sent = set(users[chat_id].get("sent_jobs", []))
        sent.add(job_id)
        users[chat_id]["sent_jobs"] = list(sent)
        save_users(users)

def get_sent_jobs(chat_id):
    users = load_users()
    return set(users.get(chat_id, {}).get("sent_jobs", []))
