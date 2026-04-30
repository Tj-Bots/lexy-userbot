from datetime import datetime, timedelta
import aiohttp
from pyrogram import Client, filters

@Client.on_message(filters.command(["link", "invite", "קישורהזמנה"], prefixes="!") & filters.me)
async def invite_handler(client, message):
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []
    
    if "-h" in args or "--help" in args:
        help_text = """
**🔗 פקודת !link - יצירת קישור הזמנה**

**דגלים:**
`-h` - מציג עזרה
`-r` - קישור שדורש אישור מנהל
`-t <שעות>` - קישור שפג תוך X שעות
`-l <מספר>` - הגבלת מספר משתמשים
`-s` - מקצר את הקישור

**דוגמאות:**
`!link` - קישור רגיל
`!link -r -s` - קישור עם אישור + מקוצר
`!link -t 2 -l 5` - פג תוך שעתיים, עד 5 משתמשים
        """
        return await message.edit(help_text.strip())
    
    hours = None
    member_limit = None
    request_required = False
    short_link = False
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "-r":
            request_required = True
        elif arg == "-s":
            short_link = True
        elif arg == "-t" and i + 1 < len(args):
            try:
                hours = int(args[i + 1])
                i += 1
            except:
                pass
        elif arg == "-l" and i + 1 < len(args):
            try:
                member_limit = int(args[i + 1])
                i += 1
            except:
                pass
        i += 1
    
    expire_date = datetime.now() + timedelta(hours=hours) if hours else None
    
    try:
        link = await client.create_chat_invite_link(
            chat_id=message.chat.id,
            member_limit=member_limit,
            expire_date=expire_date,
            creates_join_request=request_required
        )
        
        original_url = link.invite_link
        final_url = original_url
        
        if short_link:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://tinyurl.com/api-create.php?url={original_url}") as resp:
                        if resp.status == 200:
                            short = await resp.text()
                            final_url = short.strip()
            except:
                pass
        
        info_lines = []
        if hours:
            info_lines.append(f"⏰ פג תוך: {hours} שעות")
        if member_limit:
            info_lines.append(f"👥 מגבלה: {member_limit} משתמשים")
        if request_required:
            info_lines.append(f"🔐 דורש אישור מנהל")
        if short_link and final_url != original_url:
            info_lines.append(f"✂️ קוצר בהצלחה")
        
        result_text = f"**🔗 קישור הזמנה:**\n<blockquote>{final_url}</blockquote>"
        if info_lines:
            result_text += "\n\n" + "\n".join(info_lines)
        
        await message.edit(result_text)
        
    except Exception as e:
        await message.edit(f"❌ שגיאה: {e}\n\nודא שהחשבון שלך מנהל בקבוצה")