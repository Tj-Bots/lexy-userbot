import os
import asyncio
import secrets
import aiofiles
from pyrogram import Client, filters
from telegraph import Telegraph

section_dict = {"General": "🗒", "Video": "🎞", "Audio": "🔊", "Text": "🔠", "Image": "🖼", "Menu": "🗃"}

def parseinfo(out, size):
    tc = ""
    blocks = []
    lines = out.split('\n')
    
    current_header = None
    current_lines = []
    
    for line in lines:
        if not line.strip(): continue
        is_header = False
        for s in section_dict.keys():
            if line.strip().startswith(s) and ":" not in line:
                if current_header:
                    blocks.append((current_header, current_lines))
                current_header = line.strip()
                current_lines = []
                is_header = True
                break
        if not is_header:
            if not current_header: current_header = "General"
            current_lines.append(line)
    if current_header:
        blocks.append((current_header, current_lines))
        
    size_val = f"{size / (1024 * 1024):.2f} MiB"
    if size > 1024 * 1024 * 1024:
        size_val = f"{size / (1024 * 1024 * 1024):.2f} GiB"

    align_pos = 43 
    for header, content in blocks:
        for l in content:
            if ":" in l and not l.startswith(" "):
                align_pos = l.find(":")
                break
        if align_pos != 43: break

    for header, content in blocks:
        emoji = "🗒"
        for k, v in section_dict.items():
            if header.startswith(k):
                emoji = v
                break
        
        tc += f"<h4>{emoji} {header.replace('Text', 'Subtitle')}</h4><pre>"
        
        for l in content:
            if ":" in l:
                parts = l.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()
                tc += f"{key:<{align_pos}} : {val}\n"
            else:
                tc += l.strip() + "\n"
        tc += "</pre>"
        
    return tc

def create_telegraph_page(title, content, client_name):
    telegraph = Telegraph()
    telegraph.create_account(short_name=secrets.token_hex(4))
    response = telegraph.create_page(
        title=title,
        html_content=content,
        author_name=client_name
    )
    return response['url']

@Client.on_message(filters.regex(r"^!mediainfo$") & filters.me)
async def mediainfo_handler(client, message):
    if not message.reply_to_message:
        return await message.edit("❌ הגב על קובץ מדיה.")
    
    replied_msg = message.reply_to_message
    file_obj = replied_msg.video or replied_msg.document or replied_msg.audio or replied_msg.animation
    
    if not file_obj:
        return await message.edit("❌ אין מדיה מתאימה בהודעה.")

    await message.edit("__Generating MediaInfo...__")

    file_path = f"mi_{replied_msg.id}_{secrets.token_hex(2)}.dat"
    
    try:
        chunk_size = 0
        limit = 20 * 1024 * 1024 
        
        async with aiofiles.open(file_path, "wb") as f:
            async for chunk in client.stream_media(file_obj): 
                await f.write(chunk)
                chunk_size += len(chunk)
                if chunk_size > limit:
                    break

        proc = await asyncio.create_subprocess_shell(
            f'mediainfo "{file_path}"',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode().strip()

        if not output:
            return await message.edit("❌ שגיאה בהפקת המידע.")

        file_name = getattr(file_obj, "file_name", "Unknown File")
        parsed_content = parseinfo(output, file_obj.file_size)
        final_html = f"<h4>📌 {file_name}</h4><br>{parsed_content}"
        
        me = await client.get_me()
        link = await asyncio.to_thread(create_telegraph_page, "MediaInfo Result", final_html, me.first_name)
        
        await message.edit(
            f"**MediaInfo:**\n\n**➲ Link**\n{link}",
            disable_web_page_preview=False
        )

    except Exception as e:
        await message.edit(f"❌ שגיאה: `{e}`")
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
