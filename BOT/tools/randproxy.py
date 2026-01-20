from pyrogram import Client, filters
from pyrogram.types import Message
import csv
import random
import os
import httpx
import asyncio

PROXY_CSV_FILE = "FILES/proxy.csv"

def load_proxies_from_csv():
    """Load proxies from CSV file"""
    proxies = []
    if not os.path.exists(PROXY_CSV_FILE):
        return proxies
    
    with open(PROXY_CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            proxies.append({
                "host": row.get("host", ""),
                "port": row.get("port", ""),
                "username": row.get("username", ""),
                "password": row.get("password", "")
            })
    return proxies

PROXIES = load_proxies_from_csv()

def get_random_proxy() -> dict:
    """Get a random proxy from the list"""
    if not PROXIES:
        return None
    return random.choice(PROXIES)

def format_proxy(proxy: dict, format_type: str = "url") -> str:
    """Format proxy into different formats"""
    host = proxy["host"]
    port = proxy["port"]
    user = proxy["username"]
    pwd = proxy["password"]
    
    if format_type == "url":
        return f"http://{user}:{pwd}@{host}:{port}"
    elif format_type == "hostport":
        return f"{host}:{port}:{user}:{pwd}"
    elif format_type == "userhost":
        return f"{user}:{pwd}@{host}:{port}"
    return f"{host}:{port}"

async def test_proxy(proxy_url: str) -> tuple:
    """Test if proxy is working"""
    try:
        transport = httpx.AsyncHTTPTransport(proxy=proxy_url)
        async with httpx.AsyncClient(transport=transport, timeout=10) as client:
            res = await client.get("https://ipinfo.io/json")
            if res.status_code == 200:
                data = res.json()
                return True, data.get("ip"), data.get("country", "Unknown")
            return False, None, None
    except Exception as e:
        return False, None, str(e)

@Client.on_message(filters.command("rproxy"))
async def random_proxy_handler(client, message: Message):
    """Get a random proxy from the pool"""
    try:
        amount = int(message.command[1]) if len(message.command) > 1 else 1
        amount = min(amount, 10)  # Limit to 10
    except:
        amount = 1
    
    if not PROXIES:
        return await message.reply(
            "<b>No proxies available in pool ❌</b>",
            reply_to_message_id=message.id
        )
    
    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"
    
    selected_proxies = random.sample(PROXIES, min(amount, len(PROXIES)))
    
    proxy_list = []
    for proxy in selected_proxies:
        formatted = format_proxy(proxy, "hostport")
        proxy_list.append(f"<code>{formatted}</code>")
    
    reply_text = f"""<pre>Random Proxy 🔗</pre>
━━━━━━━━━━━━━━━
{chr(10).join(proxy_list)}
━━━━━━━━━━━━━━━
<b>Amount:</b> {len(selected_proxies)}
<b>Total Pool:</b> {len(PROXIES)}
<b>Requested By:</b> {profile}"""
    
    await message.reply(reply_text, reply_to_message_id=message.id)

@Client.on_message(filters.command("tproxy"))
async def test_proxy_handler(client, message: Message):
    """Get and test a random proxy"""
    if not PROXIES:
        return await message.reply(
            "<b>No proxies available in pool ❌</b>",
            reply_to_message_id=message.id
        )
    
    msg = await message.reply("<pre>Testing Proxy... 🔄</pre>", quote=True)
    
    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"
    
    proxy = get_random_proxy()
    proxy_url = format_proxy(proxy, "url")
    
    working, ip, country = await test_proxy(proxy_url)
    
    if working:
        reply_text = f"""<pre>Proxy Test Result ✅</pre>
━━━━━━━━━━━━━━━
<b>⊙ Host:</b> <code>{proxy['host']}</code>
<b>⊙ Port:</b> <code>{proxy['port']}</code>
<b>⊙ Status:</b> <code>Working ✅</code>
<b>⊙ IP:</b> <code>{ip}</code>
<b>⊙ Country:</b> <code>{country}</code>
━━━━━━━━━━━━━━━
<b>Tested By:</b> {profile}"""
    else:
        reply_text = f"""<pre>Proxy Test Result ❌</pre>
━━━━━━━━━━━━━━━
<b>⊙ Host:</b> <code>{proxy['host']}</code>
<b>⊙ Port:</b> <code>{proxy['port']}</code>
<b>⊙ Status:</b> <code>Not Working ❌</code>
<b>⊙ Error:</b> <code>{country or 'Connection Failed'}</code>
━━━━━━━━━━━━━━━
<b>Tested By:</b> {profile}"""
    
    await msg.edit_text(reply_text)

@Client.on_message(filters.command("proxyinfo"))
async def proxy_info_handler(client, message: Message):
    """Get info about the proxy pool"""
    if not PROXIES:
        return await message.reply(
            "<b>No proxies available in pool ❌</b>",
            reply_to_message_id=message.id
        )
    
    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"
    
    # Count unique hosts
    unique_hosts = len(set(p["host"] for p in PROXIES))
    
    reply_text = f"""<pre>Proxy Pool Info 📊</pre>
━━━━━━━━━━━━━━━
<b>⊙ Total Proxies:</b> <code>{len(PROXIES)}</code>
<b>⊙ Unique Hosts:</b> <code>{unique_hosts}</code>
<b>⊙ Source:</b> <code>proxy.csv</code>
━━━━━━━━━━━━━━━
<b>Commands:</b>
<code>/rproxy</code> - Get random proxy
<code>/rproxy 5</code> - Get 5 random proxies
<code>/tproxy</code> - Test a random proxy
━━━━━━━━━━━━━━━
<b>Requested By:</b> {profile}"""
    
    await message.reply(reply_text, reply_to_message_id=message.id)
