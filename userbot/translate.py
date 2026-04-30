from pyrogram import Client, filters
from deep_translator import GoogleTranslator

@Client.on_message(filters.regex(r"^!tr(?:\s+(.+))?$") & filters.me)
async def translate_handler(client, message):
    text = ""
    
    if message.matches[0].group(1):
        text = message.matches[0].group(1).strip()
    elif message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        text = message.reply_to_message.text or message.reply_to_message.caption
    else:
        return

    try:
        is_hebrew = any("\u0590" <= c <= "\u05EA" for c in text)
        target = 'en' if is_hebrew else 'iw'
        
        translated = GoogleTranslator(source='auto', target=target).translate(text)
        
        # עריכה ישירה בלי הודעות ביניים
        await message.edit(f"🔤 **תרגום ({target}):**\n\n{translated}")
        
    except:
        pass # בשביל לא לפוצץ בשגיאות אם גוגל חוסם זמנית
