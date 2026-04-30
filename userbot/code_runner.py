import asyncio
import html
import sys
import io
import time
import re
import tempfile
import json
import aiohttp
import requests
from contextlib import redirect_stdout, redirect_stderr
from io import BytesIO, StringIO
from time import perf_counter
from traceback import format_exc
from typing import Optional

import aiohttp
import requests
import pyrogram
from pyrogram import Client, enums, filters, raw, types
from pyrogram import utils as pyroutils
from pyrogram.types import LinkPreviewOptions, Message, InputMediaDocument

# ==================== UTILS ====================
class db:
    _data = {"shell": {"timeout": 60}}
    
    @staticmethod
    def get(category, key, default=None):
        return db._data.get(category, {}).get(key, default)

def command(commands):
    if isinstance(commands, str):
        commands = [commands]
    return filters.command(commands, prefixes=".")

def paste_kaizoku(text):
    """Upload text to kaizoku paste service"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "content-type": "application/json",
        }
        data = {"content": text}
        
        response = requests.post("https://paste.kaizoku.cyou/api/v1/pastes", json=data, headers=headers, timeout=30)
        if response.status_code in [200, 201]:
            result = response.json()
            paste_id = result.get("id")
            if paste_id:
                return {
                    "url": f"https://paste.kaizoku.cyou/{paste_id}",
                    "raw": f"https://paste.kaizoku.cyou/{paste_id}/raw",
                    "status": True
                }
        return None
    except Exception as e:
        print(f"Paste error: {e}")
        return None

async def shell_exec(command, timeout=60):
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    return proc.returncode, stdout.decode(), stderr.decode()

code_result = (
    "<tg-emoji emoji-id=5260480440971570446>🌐</tg-emoji>  <b>Language:</b> <code>Python</code>\n\n<b><emoji id=5431376038628171216>💻</emoji> Code:</b>\n"
    '<pre language="{pre_language}">{code}</pre>\n\n'
    "{result}"
)

# ==================== PYTHON EXECUTOR ====================
async def aexec(code, client: Client, message: Message, timeout=None):
    exec_globals = {
        "app": client,
        "client": client,
        "c": client,
        "m": message,
        "message": message,
        "r": message.reply_to_message,
        "reply": message.reply_to_message,
        "u": message.from_user,
        "ru": getattr(message.reply_to_message, "from_user", None) if message.reply_to_message else None,
        "chat": message.chat,
        "me": await client.get_me(),
        "p": print,
        "print": print,
        "here": message.chat.id,
        "db": db,
        "raw": raw,
        "types": types,
        "enums": enums,
        "pyrogram": pyrogram,
        "asyncio": asyncio,
        "aiohttp": aiohttp,
        "json": json,
        "requests": requests,
        "paste_kaizoku": paste_kaizoku,
    }

    exec(
        "async def __todo(client, message, *args):\n"
        + "".join(f"\n {_l}" for _l in code.split("\n")),
        exec_globals,
    )

    f = StringIO()

    with redirect_stdout(f):
        await asyncio.wait_for(exec_globals["__todo"](client, message), timeout=timeout)

    return f.getvalue()

@Client.on_message(command(["py", "python"]) & filters.me)
async def python_exec(client: Client, message: Message):
    if len(message.command) == 1:
        return await message.edit_text(
            "<b>Usage:</b>\n"
            "`.py print('hello')`\n"
            "`.py await client.get_me()`\n"
            "`.py p(r)` (with reply)"
        )
    
    code = message.text.split(maxsplit=1)[1]
    await message.edit_text("<b>🔄 Executing Python code...</b>")
    
    try:
        start_time = perf_counter()
        result = await aexec(code, client, message, timeout=60)
        elapsed = round(perf_counter() - start_time, 5)
    except asyncio.TimeoutError:
        return await message.edit_text(
            code_result.format(
                pre_language="python",
                code=html.escape(code),
                result="<b>❌ Timeout Error!</b>"
            ),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except Exception:
        error_text = format_exc()
        return await message.edit_text(
            f"<b>❌ Error:</b>\n<code>{html.escape(error_text)}</code>"
        )
    
    if not result:
        result = "(no output)"
    
    # Handle long output
    if len(result) > 3000:
        # Try kaizoku paste - עכשיו בלי await כי זו פונקציה רגילה!
        paste_data = paste_kaizoku(result)
        if paste_data and paste_data["status"]:
            result_text = (
                f"<b><tg-emoji emoji-id=5472164874886846699>✨</tg-emoji> Result:</b>\n"
                f"<blockquote>Output too long. <a href='{paste_data['url']}'>View full output</a></blockquote>\n\n"
                f"<i><b>Completed in {elapsed}s.</b></i>"
            )
            await message.edit_text(
                code_result.format(
                    pre_language="python",
                    code=html.escape(code),
                    result=result_text
                ),
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        else:
            # Upload as document
            bytes_io = BytesIO(result.encode())
            bytes_io.name = "output.txt"
            
            caption_text = code_result.format(
                pre_language="python",
                code=html.escape(code),
                result=f"<b><tg-emoji emoji-id=5472164874886846699>✨</tg-emoji> Result:</b>\n<blockquote>Output attached as document.</blockquote>\n\n<i><b>Completed in {elapsed}s.</b></i>"
            )
            
            await client.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.id,
                media=InputMediaDocument(
                    media=bytes_io,
                    caption=caption_text,
                    parse_mode=enums.ParseMode.HTML
                )
            )
    else:
        await message.edit_text(
            code_result.format(
                pre_language="python",
                code=html.escape(code),
                result=f"<b><tg-emoji emoji-id=5472164874886846699>✨</tg-emoji> Result:</b>\n<pre>{html.escape(result)}</pre>\n\n<i><b>Completed in {elapsed}s.</b></i>"
            ),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )

# ==================== SHELL EXECUTOR ====================
@Client.on_message(command(["sh", "shell", "term"]) & filters.me)
async def shell_executor(client: Client, message: Message):
    if len(message.command) == 1:
        return await message.edit_text(
            "<b>Usage:</b>\n"
            "`.sh ls -la`\n"
            "`.sh python3 --version`"
        )
    
    command_str = message.text.split(maxsplit=1)[1]
    await message.edit_text(f"<b>🔄 Executing: {html.escape(command_str)}</b>")
    
    try:
        start_time = perf_counter()
        rcode, stdout, stderr = await shell_exec(command_str, timeout=30)
        elapsed = round(perf_counter() - start_time, 5)
    except asyncio.TimeoutError:
        return await message.edit_text(
            f"<b>❌ Timeout Error!</b>\nCommand: <code>{html.escape(command_str)}</code>"
        )
    
    output = stdout or stderr or "(no output)"
    
    # Build base result text
    if stderr and rcode != 0:
        result_prefix = f"<b>❌ Error (code {rcode}):</b>\n"
    else:
        result_prefix = f"<b><tg-emoji emoji-id=5472164874886846699>✨</tg-emoji> Output:</b>\n"
    
    # Handle long output
    if len(output) > 3000:
        # Try kaizoku paste - בלי await!
        paste_data = paste_kaizoku(output)
        if paste_data and paste_data["status"]:
            result_text = (
                f"{result_prefix}"
                f"<blockquote>Output too long. <a href='{paste_data['url']}'>View full output</a></blockquote>\n\n"
                f"<i>Completed in {elapsed}s.</i>"
            )
            
            await message.edit_text(
                f"<b><emoji id=5431376038628171216>💻</emoji> Command:</b> <code>{html.escape(command_str)}</code>\n\n{result_text}",
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        else:
            # Upload as document
            bytes_io = BytesIO(output.encode())
            bytes_io.name = "output.txt"
            
            # חותכים פקודה ארוכה מדי
            short_cmd = command_str[:200] + "..." if len(command_str) > 200 else command_str
            
            caption_text = (
                f"<b><emoji id=5431376038628171216>💻</emoji> Command:</b> <code>{html.escape(short_cmd)}</code>\n\n"
                f"{result_prefix}<blockquote>Output attached as document.</blockquote>\n\n"
                f"<i><b>Completed in {elapsed}s.</b></i>"
            )
            
            await client.edit_message_media(
                chat_id=message.chat.id,
                message_id=message.id,
                media=InputMediaDocument(
                    media=bytes_io,
                    caption=caption_text,
                    parse_mode=enums.ParseMode.HTML
                )
            )
    else:
        result_text = f"{result_prefix}<pre>{html.escape(output)}</pre>\n\n<i><b>Completed in {elapsed}s.</b></i>"
        
        await message.edit_text(
            f"<b><emoji id=5431376038628171216>💻</emoji> Command:</b> <code>{html.escape(command_str)}</code>\n\n{result_text}",
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )