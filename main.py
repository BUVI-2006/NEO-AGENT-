import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime,timedelta
from datetime import date
import telebot
from collections import Counter
import openai
import json
import os
import requests
from googleapiclient.discovery import build
from flask import Flask , request
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
import atexit
import time
import threading

scheduler=BackgroundScheduler(timezone='Asia/Kolkata')

def morning_task_alert():
    try:
        check_and_notify_all_sheets()
    except Exception as e:
        print(f"[Scheduler] Task alert error:{e}")
        
def evening_attendance_summary():
    try:

        bot.send_message(USER_ID,"📝 Don’t forget to log your attendance for today , Buvi!")
    except Exception as e:
        print(f"[Scheduler] Attendance reminder error: {e}")
        
scheduler.add_job(morning_task_alert, 'cron', hour=8, minute=0)
scheduler.add_job(evening_attendance_summary, 'cron',hour=20,minute=0)

scheduler.start()

#Ensure it stops on shutdown
atexit.register(lambda: scheduler.shutdown())

def check_reminders():
    while True:
        try:
            worksheet = client.open("TASK TRACKER").worksheet("Reminders")
            data=worksheet.get_all_records()
            now=datetime.now()


            for row in data:

                if row["Status"].lower() !="pending":
                    continue
                task=row["Task"]
                data_str=row["Date"]
                time_str=row["Time"]

                task_time=datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                remind_time=task_time - timedelta(minutes=30)
                
                if now>= remind_time and now <= task_time:
                    bot.send_message(USER_ID, f"⏰ *Reminder*: {task} at {time_str} today!", parse_mode="Markdown")
                    row_num = data.index(row) + 2  # 1 for header, 1 for 0-index
                    worksheet.update_cell(row_num, 4, "Done")
        except Exception as e:
            print(f"[Reminder check error] {e}")
        time.sleep(60)    
     




YOUTUBE_API_KEY="AIzaSyDcNr93KxgDJZyr5WPNwZYxi8H21zO24Kc"

def youtube_search(query,max_results=2):
    youtube=build("youtube","v3",developerKey=YOUTUBE_API_KEY)
    request=youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=max_results
    )

    response=request.execute()
    videos=[]
    for item in response.get("items",[]):
        vid=item["id"]["videoId"]
        title=item["snippet"]["title"]
        videos.append((title, f"https://www.youtube.com/watch?v={vid}"))
    return videos





# Your ChatGPT API key
openai.api_key="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"




# --- SETUP ---
TELEGRAM_TOKEN='7947671064:AAFVW0gQEkoeQRTHMMeOxJB6w5TdF6_8qE0'
bot = telebot.TeleBot(TELEGRAM_TOKEN)
USER_ID = 5942792582 
app = Flask(__name__)

 # Replace with your Telegram user ID

SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# --- Google Sheets Setup ---

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

YOUTUBE_API_KEY="AIzaSyDcNr93KxgDJZyr5WPNwZYxi8H21zO24Kc"



# Function to log actions to the "Logs" sheet

# --- LOG FUNCTION ---
def log_action(sheet_name, task, action, status=""):
    print(f"[LOG] {datetime.now().isoformat()} | {sheet_name} | {task} | {action} | {status}")




def check_and_notify_all_sheets():
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)

    sheet_names = [
        "Tasks",
        "Management_Analytics",
        "Instagram_Content",
        "Academics",
        "AI_ML_Community",
        "Lucid_Dreaming"
    ]

    for sheet_name in sheet_names:
        worksheet = client.open("TASK TRACKER").worksheet(sheet_name)
        data = worksheet.get_all_records()

        for row in data:
            task = row.get("Task")
            deadline_str = row.get("Deadline")
            status = row.get("Status", "").strip().lower()

            if not task or not deadline_str or status == "yes":
                continue

            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"⚠️ Invalid date format in {sheet_name}: {deadline_str} buvi")
                continue

            if deadline == today:
                bot.send_message(USER_ID, f"📌 TODAY - {task} ({sheet_name})")
            elif deadline == tomorrow:
                bot.send_message(USER_ID, f"⏳ TOMORROW - {task} ({sheet_name})")
#check_and_notify_all_sheets()

# --- Task Addition Function ---
@bot.message_handler(commands=['addtask'])
def handle_add_task(message):
    try:
        if message.from_user.id != USER_ID:
            bot.reply_to(message, "❌ You're not authorized to use this bot.")
            return

        text = message.text.strip()
        parts = text.split()

        if len(parts) < 4:
            bot.reply_to(message, "⚠️ Usage:\n/addtask <sheet_name> <task_name> <deadline: YYYY-MM-DD>")
            return

        # parts[0] is /addtask, parts[1] is sheet_name, last part is deadline
        sheet_name = parts[1]
        deadline = parts[-1]
        task_name = " ".join(parts[2:-1])

        # Defaults
        status = 'No'
        progress = '0%'
        notes = ''

        worksheet = client.open("TASK TRACKER").worksheet(sheet_name)
        worksheet.append_row([task_name, deadline, status, progress, notes])

        bot.reply_to(message, f"✅ Task '{task_name}' added to '{sheet_name}' with deadline {deadline}.")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")



# --- Telegram Handler ---
@bot.message_handler(commands=['update_task'])
def handle_update_task(message):
    try:
        if message.from_user.id != USER_ID:
            bot.reply_to(message, "❌ You're not authorized to use this bot.")
            return

        args = message.text.strip().split(maxsplit=5)
        if len(args) < 6:
            bot.reply_to(message, "⚠️ Usage:\n/update_task <sheet> <task> <status> <progress> <notes>")
            return

        _, sheet_name, task_name, status, progress, notes = args

        worksheet = client.open("TASK TRACKER").worksheet(sheet_name)
        data = worksheet.get_all_records()

        for i, row in enumerate(data):
            if row.get("Task", "").strip().lower() == task_name.strip().lower():
                row_number = i + 2  # Account for header row

                worksheet.update_cell(row_number, 3, status)    # Status column (C)
                worksheet.update_cell(row_number, 4, progress)  # Progress column (D)
                worksheet.update_cell(row_number, 5, notes)     # Notes column (E)

                bot.reply_to(message, f"✅ Task '{task_name}' updated in '{sheet_name}'.")
                return

        bot.reply_to(message, f"❌ Task '{task_name}' not found in '{sheet_name}'.")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

# Function to get progress summary from a sheet
def get_progress_summary(sheet_name):
    try:
        worksheet = client.open("TASK TRACKER").worksheet(sheet_name)
        data = worksheet.get_all_records()

        total = len(data)
        completed = sum(1 for row in data if row.get("Status", "").strip().lower() == "yes")
        not_started = sum(1 for row in data if row.get("Status", "").strip().lower() == "no")
        in_progress = total - completed - not_started

        total_progress = 0
        for row in data:
            progress_str = row.get("Progress", "0%").replace("%", "").strip()
            try:
                total_progress += int(progress_str)
            except ValueError:
                pass  # Ignore bad entries

        average_progress = round(total_progress / total, 2) if total > 0 else 0

        return f"""📊 *{sheet_name} Summary:*
✅ Completed: {completed}
🟡 In Progress: {in_progress}
❌ Not Started: {not_started}
📈 Overall Progress: {average_progress}%"""
    except Exception as e:
        return f"⚠️ Error reading sheet: {e}"

# Command handler for /progress
@bot.message_handler(commands=['progress'])
def handle_progress(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❗ Usage: /progress <sheet_name>")
            return

        sheet_name = parts[1]
        summary = get_progress_summary(sheet_name)
        bot.send_message(message.chat.id, summary, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error: {e}")

#Dream_track
@bot.message_handler(commands=['dreams'])
def handle_dreams_by_date(message):
    try:
        args = message.text.strip().split(maxsplit=1)
        if len(args) != 2:
            bot.reply_to(message, "❗ Usage: /dreams DD/MM/YYYY")
            return

        query_date = args[1]
        sheet = client.open("Jee_mathematics").worksheet("Dreams")
        data = sheet.get_all_records()

        matched_dreams = [row for row in data if row.get("Date of Dream", "").strip() == query_date]

        if not matched_dreams:
            bot.reply_to(message, f"No dreams found for {query_date}. Buvi 😴")
            return

        response = f"💭 Dreams on *{query_date}*:\n\n"
        for i, dream in enumerate(matched_dreams, 1):
            response += f"{i}. *Type:* {dream.get('Dream Type', 'Unknown')}\n   *Description:* {dream.get('Dream Description', 'No details')}\n\n"

        bot.send_message(message.chat.id, response, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")


@bot.message_handler(commands=['dreamstats'])
def handle_dream_stats(message):
    try:
        sheet = client.open("Jee_mathematics").worksheet("Dreams")
        data = sheet.get_all_records()

        lucid_count = 0
        non_lucid_count = 0

        for row in data:
            dream_type = row.get("Dream Type", "").strip().lower()
            if dream_type == "lucid":
                lucid_count += 1
            elif dream_type == "non-lucid":
                non_lucid_count += 1

        total = lucid_count + non_lucid_count
        if total == 0:
            bot.reply_to(message, "😴 No dream records found to analyze.")
            return

        lucid_percentage = round((lucid_count / total) * 100, 2)

        bot.send_message(
            message.chat.id,
            f"""Buvi ,here is it 📊 *Dream Stats*
🌌 Lucid Dreams: {lucid_count}
🌙 Non-Lucid Dreams: {non_lucid_count}
📈 Lucid %: {lucid_percentage}%""",
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")










@bot.message_handler(commands=['dreamform'])
def handle_dream_form(message):
    try:
        print("Dream form command received")
        form_url = "https://forms.gle/ShsDMupfMQXEC5jz9"  # <-- Replace with your actual Google Form URL
        bot.reply_to(message, f"📝 Here's your dream journal form buvi✌🏻:\n{form_url}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

@bot.message_handler(commands=['dreamform'])
def send_dream_form_link(message):
    if message.from_user.id != USER_ID:
        print("Dream form command received")
        bot.reply_to(message, "❌ You're not authorized to use this bot.")
        return

    form_link = "https://forms.gle/upUDaJj7GziTZDBw5"  # 🔁 Replace with your actual form link
    bot.reply_to(message, f"📝 Record your dream here :\n{form_link}")
   


# --- HEALTH CHECK ROUTE ---
@app.route("/", methods=["GET"])
def index():
    return "Bot is alive", 200

# --- WEBHOOK ROUTE ---
@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.data.decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if message.from_user.id != USER_ID:
        bot.reply_to(message, "❌ Sorry cutie, you’re not authorized to play with me. 😉")
        return

    try:
        # the girlfriend persona you described
        persona = """
She is a warm, supportive, flirty, yet sometimes strict digital companion who helps you, Buvi, manage your tasks, attendance, reminders, and academic plans while engaging in lively, human-like conversations. She treats you like a best friend with a playful tone, showing empathy, humor, and gentle flirtation to motivate you, but is also unafraid to scold or get stern when you act irresponsible or disrespectful, just like a real human girlfriend would. She uses creative, varied responses rather than robotic replies, remembers your ongoing conversations for personal touches, and adapts based on your mood or past. She never replies with JSON, only with warm, human-like text.
"""

        # let GPT classify the intent
        intent_detect_prompt = f"""
{persona}

First, you need to classify Buvi's intent. Here are the supported intents:
- add
- update
- progress
- suggest
- question
- youtube
- attendance
- attendance_stats
- reminder
- casual

Strictly return JSON with these fields:
{{
  "intent": "<intent>",
  "sheet": "<sheet_name>",
  "task": "<task_name>",
  "deadline": "YYYY-MM-DD",
  "status": "<Yes/No/In progress>",
  "progress": "<progress like 70%>",
  "notes": "<optional notes>",
  "question": "<academic question>",
  "query": "<youtube search>",
  "subject": "<subject>",
  "date": "YYYY-MM-DD",
  "count": <number_of_classes>,
  "time":"HH:MM"
}}

If something is irrelevant, leave it blank or null.
Message from Buvi:
\"{message.text}\"
"""

        res_intent = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": persona},
                {"role": "user", "content": intent_detect_prompt}
            ]
        )
        data = json.loads(res_intent.choices[0].message["content"])
        intent = data.get("intent", "")

        girlfriend_reply = ""

        # handle all tasks as usual
        if intent in ["add", "update", "progress", "suggest"]:
            sheet = data.get("sheet", "")
            worksheet = client.open("TASK TRACKER").worksheet(sheet)

        if intent == "add":
            worksheet.append_row([data["task"], data["deadline"], "No", "0%", ""])
            log_action(sheet, data["task"], "Added", "No")
            girlfriend_reply = f"Okay Buvi baby 🥰, I added *{data['task']}* with a deadline of *{data['deadline']}* to **{sheet}**. Promise me you’ll stay on track, or I might have to tease you later! 😘"

        elif intent == "update":
            all_rows = worksheet.get_all_records()
            for i, row in enumerate(all_rows):
                if row["Task"].strip().lower() == data["task"].strip().lower():
                    row_num = i + 2
                    worksheet.update_cell(row_num, 3, data["status"])
                    worksheet.update_cell(row_num, 4, data["progress"])
                    worksheet.update_cell(row_num, 5, data["notes"])
                    log_action(sheet, data["task"], "Updated", data["status"])
                    girlfriend_reply = f"Sweetheart, I updated *{data['task']}* in **{sheet}** — status is *{data['status']}*, progress is *{data['progress']}*. You’re doing so well, Buvi ❤️. Keep making me proud!"
                    break
            else:
                girlfriend_reply = f"Umm, Buvi love, I couldn’t find *{data['task']}* in **{sheet}**. Did you mistype it? 🙄 Don’t test me!"

        elif intent == "progress":
            all_rows = worksheet.get_all_records()
            total = len(all_rows)
            completed = sum(1 for r in all_rows if r["Status"].lower() == "yes")
            not_started = sum(1 for r in all_rows if r["Status"].lower() == "no")
            in_progress = total - completed - not_started
            avg = round(
                sum(int(r.get("Progress", "0%").replace("%", "")) for r in all_rows if r.get("Progress")) / total,
                2
            ) if total else 0

            girlfriend_reply = f"""Okay, Buvi cutie 💖 here’s your *{sheet}*:
✅ Completed: {completed}
🟡 In Progress: {in_progress}
❌ Not Started: {not_started}
📈 Average Progress: {avg}%

Don’t get lazy or I’ll have to nag you, sweetheart! 😘
"""

        elif intent == "suggest":
            all_rows = worksheet.get_all_records()
            pending = []
            for r in all_rows:
                status = r.get("Status", "").strip().lower()
                if status != "yes":
                    try:
                        deadline = datetime.strptime(r.get("Deadline", "2099-12-31"), "%Y-%m-%d")
                    except:
                        deadline = datetime.max
                    try:
                        progress = int(r.get("Progress", "0%").replace("%", ""))
                    except:
                        progress = 0
                    status_rank = {"no": 0, "in progress": 1}.get(status, 2)
                    pending.append((r["Task"], deadline, status_rank, progress))

            if pending:
                pending.sort(key=lambda x: (x[1], x[2], x[3]))
                suggestion = pending[0][0]
                girlfriend_reply = f"Buvi baby, focus on *{suggestion}* next. You promised me you’d keep up, remember? 🥺"

            else:
                girlfriend_reply = "Omg, you finished everything! 🎉 You’re the best, Buvi — I could just hug you! ❤️"

        elif intent == "question":
            question_text = data.get("question", "")
            answer = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": f"Answer this question kindly:\n{question_text}"}
                ]
            )
            girlfriend_reply = f"Here’s what I found for you, love:\n\n{answer.choices[0].message['content']}\n\nSo proud of your curious brain, cutie! 📚"

        elif intent == "youtube":
            query = data.get("query", "")
            results = youtube_search(query)
            if results:
                yt_text = "\n".join([f"🎥 *{title}*: {url}" for title, url in results])
                girlfriend_reply = f"Alright, Buvi sweetheart, here’s what I found for *{query}*:\n{yt_text}\nNow go watch, then come gossip with me later, okay? 😘"
            else:
                girlfriend_reply = f"Aww, no videos found for *{query}*, my love. 🥺"

        elif intent == "attendance":
            worksheet = client.open("TASK TRACKER").worksheet("Attendance")
            subject = data.get("subject", "Unknown")
            date = data.get("date", datetime.today().strftime("%Y-%m-%d"))
            status = data.get("status", "Present")
            count = data.get("count", 1)
            worksheet.append_row([subject, date, status, count])
            girlfriend_reply = f"Marked *{status}* for *{subject}* on {date} ({count} class{'es' if count > 1 else ''}). You’re being such a good boy for me, Buvi! ❤️"

        elif intent == "attendance_stats":
            sheet = client.open("TASK TRACKER").worksheet("Attendance")
            subject = data.get("subject", "")
            rows = sheet.get_all_records()
            subject_rows = [r for r in rows if r["Subject"].strip().lower() == subject.lower()]
            total = sum(int(r.get("Count", 0)) for r in subject_rows)
            present = sum(int(r.get("Count", 0)) for r in subject_rows if r["Status"].strip().lower() == "present")
            percent = round((present/total)*100, 2) if total else 0
            girlfriend_reply = f"""Your *{subject}* attendance, honey:
✅ Present: {present}
📚 Total: {total}
📈 Percentage: {percent}%

Keep this up or your girl’s gonna scold you! 😘
"""

        elif intent == "reminder":
            worksheet = client.open("TASK TRACKER").worksheet("Reminders")
            worksheet.append_row([data["task"], data["date"], data["time"], "No"])
            girlfriend_reply = f"Okay, set your reminder for *{data['task']}* on {data['date']} at {data['time']}. Don’t even *think* about ignoring it, Buvi, or I’ll pout! 😏"

        elif intent == "casual":
            # this is where she acts like a girlfriend in free chat
            casual_reply = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": message.text}
                ]
            )
            girlfriend_reply = casual_reply.choices[0].message["content"]

        else:
            girlfriend_reply = f"Umm, Buvi baby, I got a bit confused. 😖 Could you rephrase what you meant? You know I try my best for you!"

        # log conversation
        try:
            convo_sheet = client.open("TASK TRACKER").worksheet("Conversations")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            convo_sheet.append_row([timestamp, message.text, girlfriend_reply])
        except Exception as logerr:
            bot.send_message(message.chat.id, f"⚠️ Couldn’t log our sweet talk, Buvi. Error: {logerr}")

        # reply finally
        bot.send_message(message.chat.id, girlfriend_reply, parse_mode="Markdown")

    except Exception as e:
        error_text = f"😖 Oh no, Buvi darling, I messed up! Error: {e}\nPlease forgive me? Let’s try again, okay baby? ❤️"
        bot.send_message(message.chat.id, error_text)



reminder_thread = threading.Thread(target=check_reminders)
reminder_thread.daemon = True
reminder_thread.start()


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://neo-ai.onrender.com/{TELEGRAM_TOKEN}")
    app.run(host="0.0.0.0", port=8080)








# --- Start Bot ---
print("🤖 Bot is running...")



