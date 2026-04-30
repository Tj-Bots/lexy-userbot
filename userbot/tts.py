from pyrogram import Client, filters
from gtts import gTTS
from io import BytesIO
import asyncio
import os

def convert_to_audio(text):
    lang = 'iw' if any("\u0590" <= c <= "\u05EA" for c in text) else 'en'
    
    tts = gTTS(text=text, lang=lang)
    audio_file = BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.name = "tts.mp3"
    audio_file.seek(0)
    return audio_file

@Client.on_message(filters.regex(r"^!(tts|שמע)(?:\s+(.+))?$") & filters.me)
async def tts_handler(client, message):
    text = ""
    
    if message.matches[0].group(2):
        text = message.matches[0].group(2).strip()
    elif message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        text = message.reply_to_message.text or message.reply_to_message.caption
    else:
        return await message.edit("⚠️ שימוש שגוי.\nתגיב !tts על הודעה או כתוב טקסט ליד הפקודה.")

    await message.edit("**<tg-emoji emoji-id='6030555621739205413'>🎧</tg-emoji> מעבד סאונד...**")

    try:
        loop = asyncio.get_running_loop()
        audio = await loop.run_in_executor(None, convert_to_audio, text)
        
        await client.send_voice(
            chat_id=message.chat.id,
            voice=audio,
            reply_to_message_id=message.reply_to_message.id if message.reply_to_message else message.id
        )
        await message.delete()
        
    except Exception as e:
        await message.edit(f"❌ שגיאה: {e}")
