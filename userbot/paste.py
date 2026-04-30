import os
import requests
import json
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36",
    "content-type": "application/json",
}

def get_extension_from_language(lang):
    lang_map = {
        "python": "py", "py": "py",
        "javascript": "js", "js": "js",
        "typescript": "ts", "ts": "ts",
        "html": "html", "htm": "html",
        "css": "css",
        "json": "json",
        "bash": "sh", "sh": "sh", "shell": "sh",
        "ruby": "rb", "rb": "rb",
        "php": "php",
        "java": "java",
        "c": "c", "cpp": "cpp", "c++": "cpp",
        "go": "go",
        "rust": "rs", "rs": "rs",
        "sql": "sql",
        "yaml": "yml", "yml": "yml",
        "markdown": "md", "md": "md",
        "text": "txt", "txt": "txt"
    }
    return lang_map.get(lang.lower(), "txt")

def extract_code_from_entities(message):
    content = message.text or message.caption
    if not content:
        return None, None
    
    if not message.entities:
        return None, None
    
    for entity in message.entities:
        if entity.type == MessageEntityType.PRE:
            language = entity.language or "txt"
            code = content[entity.offset:entity.offset + entity.length]
            return code.strip(), language
    
    return None, None

def p_paste(message, extension=None):
    siteurl = "https://paste.kaizoku.cyou/api/v1/pastes"
    data = {"content": message}
    try:
        response = requests.post(url=siteurl, data=json.dumps(data), headers=headers)
        if response.ok:
            resp_json = response.json()
            if extension and extension != "txt":
                purl = f"https://paste.kaizoku.cyou/{resp_json['id']}.{extension}"
            else:
                purl = f"https://paste.kaizoku.cyou/{resp_json['id']}"
            return {
                "url": purl,
                "raw": f"https://paste.kaizoku.cyou/{resp_json['id']}/raw",
                "status": True
            }
        return {"status": False, "error": "Unable to reach paste service"}
    except Exception as e:
        return {"status": False, "error": str(e)}

@Client.on_message(filters.command(["paste"], prefixes="!"))
async def paste_handler(client, message):
    status_msg = message
    await status_msg.edit("[<tg-emoji emoji-id='5220046725493828505'>✍️</tg-emoji>] Processing...")
    
    content = ""
    detected_ext = None
    
    if len(message.command) > 1:
        content = message.text.split(None, 1)[1]
    
    elif message.reply_to_message:
        if message.reply_to_message.document:
            if message.reply_to_message.document.file_size > 1048576:
                return await status_msg.edit("[✘] File too large (max 1MB).")
            
            try:
                file_path = await message.reply_to_message.download()
                file_name = message.reply_to_message.document.file_name
                if file_name and "." in file_name:
                    detected_ext = file_name.split(".")[-1].lower()
                else:
                    detected_ext = None
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                os.remove(file_path)
            except Exception as e:
                return await status_msg.edit(f"[✘] Error: {e}")
        
        else:
            code_content, lang = extract_code_from_entities(message.reply_to_message)
            if code_content:
                content = code_content
                detected_ext = get_extension_from_language(lang)
                if detected_ext == "txt":
                    detected_ext = None
            else:
                content = message.reply_to_message.text or message.reply_to_message.caption
                detected_ext = None
    
    if not content:
        return await status_msg.edit("[✘] No content found.")
    
    ext_display = f".{detected_ext}" if detected_ext else "no extension"
    
    result = p_paste(content, detected_ext)
    
    if result["status"]:
        ext_text = f" as .{detected_ext}" if detected_ext else ""
        text = (
            f"**[<tg-emoji emoji-id='5219943216781995020'>⚡</tg-emoji>] Uploaded to Pasty{ext_text}**\n\n"
            f"**➲ Link:** <blockquote>{result['url']}</blockquote>\n"
            f"**➲ RAW:** <blockquote>{result['raw']}</blockquote>"
        )
        await status_msg.edit(text, disable_web_page_preview=True)
        await message.react("⚡")
    else:
        await status_msg.edit(f"[✘] Error: {result['error']}")