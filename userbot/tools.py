from pyrogram import Client, filters
import json
import aiohttp
import base64
import os
import urllib.parse
from io import BytesIO
from bs4 import BeautifulSoup

@Client.on_message(filters.regex(r"^!id$") & filters.me)
async def id_handler(client, message):
    text = f"💜 **ID Info:**\n"
    text += f"👤 **משתמש:** `{message.from_user.id}`\n"
    text += f"💬 **צ'אט:** `{message.chat.id}`\n"
    
    if message.reply_to_message:
        replied = message.reply_to_message
        text += f"\n🔄 **ריפליי אל:**\n"
        if replied.from_user:
            text += f"🆔 **משתמש:** `{replied.from_user.id}`\n"
        text += f"🔢 **הודעה:** `{replied.id}`"
    
    await message.edit(text)

@Client.on_message(filters.regex(r"^!json$") & filters.me)
async def json_handler(client, message):
    target = message.reply_to_message if message.reply_to_message else message
    raw_json = json.dumps(json.loads(str(target)), indent=2, ensure_ascii=False)
    
    if len(raw_json) > 4100:
        raw_json = raw_json[:4100] + "\n..."
        
    await message.edit(f"ℹ️ **Message JSON:**\n<pre>{raw_json}</pre>")


@Client.on_message(filters.command(["short", "קצרקישור"], prefixes="!") & filters.me)
async def short_handler(client, message):
    if len(message.command) < 2:
        return await message.edit("🔗 !short https://example.com/long/url")
    
    url = message.command[1]
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://tinyurl.com/api-create.php?url={url}") as resp:
            short = await resp.text()
    
    await message.edit(f"**✅ קישור מקוצר:**\n<blockquote>{short}</blockquote>")


@Client.on_message(filters.command(["reverse", "הפוך"], prefixes="!") & filters.me)
async def reverse_handler(client, message):
    if len(message.command) < 2:
        if message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
            text = message.reply_to_message.text or message.reply_to_message.caption
        else:
            return await message.edit("🔄 !reverse טקסט\nאו תגיב להודעה")
    else:
        text = " ".join(message.command[1:])
    
    reversed_text = text[::-1]
    await message.edit(f"{reversed_text}")