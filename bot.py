import telebot
import requests
import time
import os

# --- CONFIGURATION ---
# Ye values Railway/Koyeb ke "Variables" section se auto-load hongi
API_KEY = os.getenv("RUNWAY_API_KEY")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

# Temporary storage pichli video ki ID yaad rakhne ke liye (Long Version Continuation)
user_last_video = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 Runway Gen-3 Video Bot Taiyar Hai!\n\nBas ek prompt likhein aur main video bana dunga.\n\n*Tip: Lambi video ke liye pehli video banne ke baad 'Continue' likhein.*")

@bot.message_handler(func=lambda message: True)
def handle_video_request(message):
    user_id = message.chat.id
    prompt = message.text

    # Check agar user continuation mang raha hai
    parent_id = None
    if prompt.lower().startswith("continue") and user_id in user_last_video:
        parent_id = user_last_video[user_id]
        bot.reply_to(message, "🔄 Pichli video ko aage badha raha hoon (Continuation Mode)...")
    else:
        bot.reply_to(message, f"🎬 Video ban rahi hai: '{prompt}'\nIsme 1-2 minute lag sakte hain...")

    # Runway API Details
    url = "https://api.runwayml.com/v1/tasks"
    headers = {
        "X-Runway-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }

    # Payload for Gen-3 Alpha Turbo
    payload = {
        "taskType": "gen3a_turbo",
        "input": {
            "promptText": prompt,
            "duration": 10
        }
    }
    
    # Agar continuation hai toh pichli ID attach karein
    if parent_id:
        payload["input"]["previousTaskId"] = parent_id

    try:
        response = requests.post(url, json=payload, headers=headers)
        task_id = response.json().get("id")
        
        if not task_id:
            bot.reply_to(message, "❌ Error: API Key sahi nahi hai ya credits khatam ho gaye hain.")
            return

        # Polling Loop: Har 10 second mein check karega ki video bani ya nahi
        while True:
            status_res = requests.get(f"{url}/{task_id}", headers=headers)
            status_data = status_res.json()
            status = status_data.get("status")

            if status == "SUCCEEDED":
                video_url = status_data.get("output")[0]
                bot.send_video(user_id, video_url, caption="✅ Aapki video taiyar hai!")
                # Agli baar extend karne ke liye ID save karein
                user_last_video[user_id] = task_id
                break
            elif status == "FAILED":
                bot.reply_to(message, "❌ Video generation fail ho gayi. Dobara koshish karein.")
                break
            
            time.sleep(10)

    except Exception as e:
        bot.reply_to(message, f"⚠️ Kuch तकनीकी error aayi: {str(e)}")

# Bot ko start karne ke liye
bot.polling()
