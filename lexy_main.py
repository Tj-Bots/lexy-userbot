import os
import time
from pyrogram import Client, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

if not all([API_ID, API_HASH, SESSION_STRING]):
    print("❌ Missing environment variables! Please check your .env file.")
    exit(1)

app = Client(
    "lexy_userbot",
    api_id=int(API_ID),
    api_hash=API_HASH,
    session_string=SESSION_STRING,
    plugins=dict(root="userbot")
)

@app.on_message(filters.regex(r"^!help$") & filters.me)
async def help_handler(client, message):
    help_text = """<tg-emoji emoji-id='6026236216079290036'>💜</tg-emoji> **פקודות לקסי:**

<tg-emoji emoji-id='5305265301917549162'>📎</tg-emoji>**כלים ופלאגינים:**
<blockquote>• `!id` - מזהי משתמשים וצ'אט
• `!tr` - תרגום מהיר (ריפליי)
• `!tts` / `!שמע` - טקסט לדיבור
• `!json` - הצגת JSON של הודעה
• `!short` / `!קצרקישור` - קצר קישור
• `!paste` - העלאת קוד ל-paty
• `!search` - חיפוש טורנטים 
• `!remind` - קביעת תזכורת
• `!mediainfo` - פרטי מדיה טכניים</blockquote>

<tg-emoji emoji-id='5251203410396458957'>🛡</tg-emoji>**ניהול קבוצה:**
<blockquote>• `!נעץ` / `!בטלנעיצה` - ניהול הודעות
• `!חסום` / `!הסר` / `!ביטולחסימה`
• `!מחק` - מחיקה מהירה
• `!tagall` - תיוג כל המשתתפים
• `!קישורהזמנה` / `!link` צור קישור הזמנה לקבוצה</blockquote>

<tg-emoji emoji-id='5224607267797606837'>☄️</tg-emoji>**אחר:**
<blockquote>• `!help` - תפריט העזרה</blockquote>"""
    await message.reply(help_text)

if __name__ == "__main__":
    print(f"[{time.strftime('%H:%M:%S')}] 💜 Lexy Userbot is starting...")
    app.run()
