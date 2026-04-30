from pyrogram import Client, filters
import asyncio
import dateparser
from datetime import datetime

@Client.on_message(filters.regex(r"^!remind\s+(.+)$") & filters.me)
async def remind_handler(client, message):
    args = message.matches[0].group(1).split(maxsplit=1)
    if len(args) < 2: return
    
    time_str = args[0]
    remind_text = args[1]
    
    target_time = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'future'})
    if not target_time: return
    
    now = datetime.now()
    if target_time <= now: return
    
    delay = (target_time - now).total_seconds()
    
    await message.edit(f"💜 **תזכורת נקבעה!**\n⏰ בעוד {time_str}\n📝 `{remind_text}`")
    
    await asyncio.sleep(delay)
    
    # הודעה בפרטי
    await client.send_message(
        chat_id="me",
        text=f"🔔 **תזכורת לקסי!**\n\n📝 `{remind_text}`"
    )
    # הודעה בצ'אט המקורי
    try:
        if message.chat.id != (await client.get_me()).id:
            await client.send_message(
                chat_id=message.chat.id,
                text=f"🔔 **תזכורת!**\n\n📝 `{remind_text}`",
                reply_to_message_id=message.id
            )
    except:
        pass
