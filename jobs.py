from storage import load_users, get_sent_jobs, add_sent_job
from telegram import send_telegram

def notify_users(jobs):
    users = load_users()

    for chat_id in users.keys():
        sent = get_sent_jobs(chat_id)
        new_jobs = [j for j in jobs if j["id"] not in sent]

        if not new_jobs:
            continue

        msg = ""
        for j in new_jobs[:5]:
            msg += f"{j['title']} – {j['company']}\nhttps://technopark.in/job-details/{j['id']}\n\n"
            add_sent_job(chat_id, j["id"])

        send_telegram(chat_id, msg)
