import os
import asyncio
from pyrogram import Client, filters, enums

async def is_admin(client, chat_id):
    try:
        member = await client.get_chat_member(chat_id, "me")
        return member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]
    except:
        return False

@Client.on_message(filters.regex(r"^!נעץ$") & filters.me)
async def pin_handler(client, message):
    if not await is_admin(client, message.chat.id): return
    if not message.reply_to_message: return
    try:
        await message.reply_to_message.pin(disable_notification=True)
        await message.delete()
    except: pass

@Client.on_message(filters.regex(r"^!בטלנעיצה$") & filters.me)
async def unpin_handler(client, message):
    if not await is_admin(client, message.chat.id): return
    if not message.reply_to_message: return
    try:
        await message.reply_to_message.unpin()
        await message.delete()
    except: pass

@Client.on_message(filters.regex(r"^!הסר$") & filters.me)
async def kick_handler(client, message):
    if not await is_admin(client, message.chat.id): return
    from userbot.managroup import get_target_user
    user = await get_target_user(client, message)
    if not user: return
    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await message.edit(f"👋 {user.mention} הוסר מהקבוצה.")
    except Exception as e: await message.edit(f"❌ שגיאה: {e}")

@Client.on_message(filters.regex(r"^!מחק$") & filters.me)
async def delete_handler(client, message):
    if not message.reply_to_message: return
    try:
        await message.reply_to_message.delete()
        await message.delete()
    except: pass

@Client.on_message(filters.regex(r"^!tagall$") & filters.me)
async def tag_all_handler(client, message):
    if not await is_admin(client, message.chat.id): return
    
    await message.edit("💜 **מתייגת את כולם...**")
    mentions = ""
    count = 0
    
    async for member in client.get_chat_members(message.chat.id):
        if member.user.is_bot or member.user.is_deleted:
            continue
        
        mentions += f"{member.user.mention} "
        count += 1
        
        if count == 50:
            try:
                await client.send_message(message.chat.id, mentions)
                mentions = ""
                count = 0
                await asyncio.sleep(1) # מניעת פלוד
            except: pass
            
    if mentions:
        await client.send_message(message.chat.id, mentions)
    
    await message.delete()

async def get_target_user(client, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    cmd_parts = message.text.split()
    if len(cmd_parts) > 1:
        user_input = cmd_parts[1]
        try:
            if user_input.isdigit(): return await client.get_users(int(user_input))
            else: return await client.get_users(user_input)
        except: return None
    return None
