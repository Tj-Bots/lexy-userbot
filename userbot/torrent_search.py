import asyncio
import secrets
import aiohttp
import json
from pyrogram import Client, filters
from telegraph import Telegraph
from bs4 import BeautifulSoup
from urllib.parse import quote

def create_telegraph_page(title, content, client_name):
    telegraph = Telegraph()
    telegraph.create_account(short_name=secrets.token_hex(4))
    response = telegraph.create_page(title=title, html_content=content, author_name=client_name)
    return response['url']

async def fetch_url(session, url):
    try:
        async with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=15) as resp:
            return await resp.text() if resp.status == 200 else None
    except:
        return None

def format_size(size_bytes):
    try:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
    except:
        return "N/A"

async def search_piratebay(session, encoded):
    results = []
    try:
        tpb_data = await fetch_url(session, f"https://apibay.org/q.php?q={encoded}")
        if tpb_data:
            tpb_json = json.loads(tpb_data)
            if isinstance(tpb_json, list) and tpb_json and tpb_json[0].get('id') != '0':
                for item in tpb_json[:25]:
                    name = item.get("name")
                    if name:
                        results.append({
                            "name": name,
                            "size": format_size(item.get("size")),
                            "seeders": item.get("seeders", "0"),
                            "leechers": item.get("leechers", "0"),
                            "magnet": f"magnet:?xt=urn:btih:{item.get('info_hash')}&dn={quote(name)}",
                            "info_url": f"https://thepiratebay.org/description.php?id={item.get('id')}",
                            "source": "🏴‍☠️ PirateBay"
                        })
    except Exception as e:
        print(f"PirateBay error: {e}")
    return results

async def search_limetorrents(session, encoded):
    results = []
    try:
        page_lime = await fetch_url(session, f"https://www.limetorrents.info/search/all/{encoded}/")
        if page_lime:
            soup = BeautifulSoup(page_lime, 'html.parser')
            rows = soup.select('table.table2 tr')[1:25]
            for row in rows:
                try:
                    tds = row.select('td')
                    if len(tds) < 4:
                        continue
                    link_tag = tds[0].select('a')[-1]
                    name = link_tag.text.strip()
                    info_url = "https://www.limetorrents.info" + link_tag['href']
                    p_text = await fetch_url(session, info_url)
                    if p_text:
                        mag_tag = BeautifulSoup(p_text, 'html.parser').select_one('a[href^="magnet:"]')
                        if mag_tag and name:
                            results.append({
                                "name": name,
                                "size": tds[2].text.strip(),
                                "seeders": tds[3].text.strip(),
                                "leechers": "N/A",
                                "magnet": mag_tag['href'],
                                "info_url": info_url,
                                "source": "🍋 LimeTorrents"
                            })
                except Exception:
                    continue
    except Exception as e:
        print(f"LimeTorrents error: {e}")
    return results

async def search_nyaa(session, encoded):
    results = []
    try:
        page_nyaa = await fetch_url(session, f"https://nyaa.si/?q={encoded}&f=0&c=0_0&s=seeders&o=desc")
        if page_nyaa:
            soup = BeautifulSoup(page_nyaa, 'html.parser')
            rows = soup.select('table.table-striped tbody tr')[:20]
            for row in rows:
                try:
                    cells = row.select('td')
                    if len(cells) < 4:
                        continue
                    
                    name_tag = cells[1].find_all('a')[-1]
                    name = name_tag.text.strip()
                    info_url = "https://nyaa.si" + name_tag.get('href', '')
                    
                    magnet_tag = cells[2].find('a', href=lambda x: x and x.startswith('magnet:'))
                    if magnet_tag and name:
                        results.append({
                            "name": name[:150],
                            "size": cells[3].text.strip() if len(cells) > 3 else "N/A",
                            "seeders": cells[5].text.strip() if len(cells) > 5 else "0",
                            "leechers": cells[6].text.strip() if len(cells) > 6 else "0",
                            "magnet": magnet_tag['href'],
                            "info_url": info_url,
                            "source": "🇯🇵 Nyaa.si"
                        })
                except Exception:
                    continue
    except Exception as e:
        print(f"Nyaa error: {e}")
    return results

@Client.on_message(filters.regex(r"^!search (.*)") & filters.me)
async def search_handler(client, message):
    query = message.matches[0].group(1)
    status_msg = await message.edit(f"<tg-emoji emoji-id='5231012545799666522'>🔍</tg-emoji> **Searching for:** `{query}`...")
    
    encoded = quote(query)
    
    async with aiohttp.ClientSession() as session:
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    search_piratebay(session, encoded),
                    search_limetorrents(session, encoded),
                    search_nyaa(session, encoded),
                    return_exceptions=True
                ),
                timeout=45
            )
        except asyncio.TimeoutError:
            await status_msg.edit(f"⏰ **Timeout:** Search took too long. Try again with a more specific query.")
            return
    
    all_results = []
    for r in results:
        if isinstance(r, Exception):
            print(f"Search error: {r}")
            continue
        if isinstance(r, list):
            all_results.extend(r)
    
    if not all_results:
        return await status_msg.edit(f"<tg-emoji emoji-id='5226660202035554522'>✖️</tg-emoji> **No results found for:** `{query}`")
    
    all_results.sort(key=lambda x: int(x.get('seeders', 0) or 0), reverse=True)
    all_results = all_results[:100]
    
    html_content = f"<h3>🔍 Search Results for: {query}</h3><hr><br>"
    
    for i, r in enumerate(all_results, 1):
        share_link = f"https://t.me/share/url?url=%60%60%60{quote(r['magnet'])}%60%60%60"
        
        html_content += f"<b>{i}. <a href='{r['info_url']}'>{r['name'][:100]}</a></b>"
        html_content += f"<blockquote>"
        html_content += f"📦 <b>Size:</b> {r['size']}<br>"
        html_content += f"🟢 <b>Seeds:</b> {r['seeders']} | 🔴 <b>Leech:</b> {r['leechers']}<br>"
        html_content += f"🌐 <b>Source:</b> {r['source']}<br><br>"
        html_content += f"📤 <a href='{share_link}'><b>Share Magnet to Telegram</b></a>"
        html_content += f"</blockquote><br> <br>"
    
    me = await client.get_me()
    try:
        page_url = await asyncio.to_thread(create_telegraph_page, f"Results for: {query}", html_content, me.first_name or "User")
        
        sources_count = {}
        for x in all_results:
            src = x['source'].split()[-1]
            sources_count[src] = sources_count.get(src, 0) + 1
        
        sources_text = " | ".join([f"**{src}:** `{count}`" for src, count in sources_count.items()])
        
        await status_msg.edit(
            f"<tg-emoji emoji-id='5206607081334906820'>✔️</tg-emoji> **Found {len(all_results)} results for `{query}`**\n"
            f"<blockquote>{sources_text}</blockquote>\n\n"
            f"<tg-emoji emoji-id='5271604874419647061'>🔗</tg-emoji> **Telegraph Page:**\n{page_url}",
            disable_web_page_preview=False
        )
    except Exception as e:
        await status_msg.edit(f"<tg-emoji emoji-id='5226660202035554522'>✖️</tg-emoji> **Error creating page:** `{e}`")
