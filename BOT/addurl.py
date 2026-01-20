import os
import json
import time
import httpx
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

SITES_PATH = "DATA/sites.json"
TEST_CARD = "4403934091847371|06|2026|097"

# AutoStripe API Config
AUTOSTRIPE_BASE_URL = "https://blackxcard-autostripe.onrender.com"
AUTOSTRIPE_GATEWAY = "autostripe"
AUTOSTRIPE_KEY = "Blackxcard"

# Error responses that mean site is not supported
NOT_SUPPORTED_KEYWORDS = [
    "failed to extract",
    "nonce",
    "not found",
    "invalid site",
    "error",
    "timeout",
    "connection",
    "unable to",
    "cannot",
    "blocked"
]

def is_site_supported(response_text):
    """Check if the response indicates the site is supported"""
    response_lower = response_text.lower()
    for keyword in NOT_SUPPORTED_KEYWORDS:
        if keyword in response_lower:
            return False
    return True

@Client.on_message(filters.command("addurl") & filters.private)
async def add_autostripe_site(client, message: Message):
    """Add AutoStripe site for user"""
    if len(message.command) < 2:
        return await message.reply(
            "❌ Please provide a site URL.\n\nExample:\n<code>/addurl dilaboards.com</code>",
            parse_mode=ParseMode.HTML
        )
    
    site = message.command[1]
    site = site.replace("https://", "").replace("http://", "").strip("/")
    
    user_id = str(message.from_user.id)
    
    wait_msg = await message.reply(
        "<pre>[🔍 Checking AutoStripe Site..! ]</pre>",
        reply_to_message_id=message.id
    )
    
    start_time = time.time()
    
    try:
        url = f"{AUTOSTRIPE_BASE_URL}/gateway={AUTOSTRIPE_GATEWAY}/key={AUTOSTRIPE_KEY}/site={site}/cc={TEST_CARD}"
        
        async with httpx.AsyncClient(timeout=90.0) as http_client:
            response = await http_client.get(url)
            response_text = response.text.strip()
        
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        # Check if site is supported
        if not response_text or not is_site_supported(response_text):
            return await wait_msg.edit_text(
                "<pre>Site Not Supported ❌</pre>",
                parse_mode=ParseMode.HTML
            )
        
        gate_name = "AutoStripe"
        
        os.makedirs("DATA", exist_ok=True)
        
        all_sites = {}
        if os.path.exists(SITES_PATH):
            try:
                with open(SITES_PATH, "r", encoding="utf-8") as f:
                    all_sites = json.load(f)
            except:
                all_sites = {}
        
        all_sites[user_id] = {
            "site": site,
            "gate": gate_name
        }
        
        with open(SITES_PATH, "w", encoding="utf-8") as f:
            json.dump(all_sites, f, indent=4)
        
        clickableFname = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
        
        return await wait_msg.edit_text(
            f"""<pre>Site Added ✅ ~ AutoStripe ✦</pre>
[⌯] <b>Site:</b> <code>{site}</code> 
[⌯] <b>Gateway:</b> <code>{gate_name}</code> 
[⌯] <b>Cmd:</b> <code>/str</code> | <code>/mstr</code>
[⌯] <b>Time:</b> <code>{time_taken}s</code> 
━━━━━━━━━━━━━
[⌯] <b>Req By:</b> {clickableFname}""",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    
    except httpx.TimeoutException:
        return await wait_msg.edit_text(
            "<pre>Site Not Supported ❌</pre>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        return await wait_msg.edit_text(
            "<pre>Site Not Supported ❌</pre>",
            parse_mode=ParseMode.HTML
        )


@Client.on_message(filters.command("mysite") & filters.private)
async def show_my_site(client, message: Message):
    """Show user's current AutoStripe site"""
    user_id = str(message.from_user.id)
    clickableFname = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    
    if not os.path.exists(SITES_PATH):
        return await message.reply(
            "<pre>No Site Found ❌</pre>\n<b>Use /addurl to add a site.</b>",
            parse_mode=ParseMode.HTML
        )
    
    try:
        with open(SITES_PATH, "r", encoding="utf-8") as f:
            all_sites = json.load(f)
    except:
        return await message.reply(
            "<pre>No Site Found ❌</pre>\n<b>Use /addurl to add a site.</b>",
            parse_mode=ParseMode.HTML
        )
    
    user_site = all_sites.get(user_id)
    
    if not user_site:
        return await message.reply(
            "<pre>No Site Found ❌</pre>\n<b>Use /addurl to add a site.</b>",
            parse_mode=ParseMode.HTML
        )
    
    await message.reply(
        f"""<pre>Your AutoStripe Site ~ Sos ✦</pre>
[⌯] <b>Site:</b> <code>{user_site['site']}</code>
[⌯] <b>Gateway:</b> <code>{user_site.get('gate', 'AutoStripe')}</code>
━━━━━━━━━━━━━
[⌯] <b>Cmd:</b> <code>/str</code> | <code>/mstr</code>
[⌯] <b>Req By:</b> {clickableFname}""",
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.command("delsite") & filters.private)
async def delete_my_site(client, message: Message):
    """Delete user's AutoStripe site"""
    user_id = str(message.from_user.id)
    
    if not os.path.exists(SITES_PATH):
        return await message.reply("<pre>No Site Found ❌</pre>", parse_mode=ParseMode.HTML)
    
    try:
        with open(SITES_PATH, "r", encoding="utf-8") as f:
            all_sites = json.load(f)
    except:
        return await message.reply("<pre>No Site Found ❌</pre>", parse_mode=ParseMode.HTML)
    
    if user_id not in all_sites:
        return await message.reply("<pre>No Site Found ❌</pre>", parse_mode=ParseMode.HTML)
    
    del all_sites[user_id]
    
    with open(SITES_PATH, "w", encoding="utf-8") as f:
        json.dump(all_sites, f, indent=4)
    
    await message.reply(
        "<pre>Site Removed ✅</pre>\n<b>Use /addurl to add a new site.</b>",
        parse_mode=ParseMode.HTML
    )
