# BOT/helper/start.py

import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from datetime import datetime
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from pyrogram.types import CallbackQuery
import html
import pytz

def clean_text(text):
    if not text:
        return "N/A"
    return html.unescape(text)

@Client.on_message(filters.command("start") & ~filters.edited)
async def start_command(client: Client, message: Message):
    animated_texts = ["〔", "〔S", "〔So", "〔Sos", "〔SosChk〕"]

    sent = await message.reply("<pre>〔</pre>", quote=True)

    for text in animated_texts[1:]:
        await asyncio.sleep(0.2)
        await sent.edit_text(f"<pre>{text}</pre>")

    # User's display name
    name = message.from_user.first_name
    if message.from_user.last_name:
        name += f" {message.from_user.last_name}"
    profile = f"<a href='tg://user?id={message.from_user.id}'>{name}</a>"

    final_text = f"""
[<a href='https://t.me/xyz'>⛯</a>] <b>Sos | Version - 1.0</b>
<pre>Constantly Upgrading...</pre>
━━━━━━━━━━━━━
<b>Hello,</b> {profile}
<i>How Can I Help You Today.?! 📊</i>
⌀ <b>Your UserID</b> - <code>{message.from_user.id}</code>
⛶ <b>BOT Status</b> - <code>Online 🟢</code>
⎔ <b>Explore</b> - <b>Click the buttons below to discover</b>
<b>all the features we offer!</b>
"""

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Register", callback_data="register"),
            InlineKeyboardButton("Commands", callback_data="home")
        ],
        [
            InlineKeyboardButton("Close", callback_data="close")
        ]
    ])

    await asyncio.sleep(0.5)
    await sent.edit_text(final_text.strip(), reply_markup=keyboard, disable_web_page_preview=True)

# BOT/helper/start.py

USERS_FILE = "DATA/users.json"
CONFIG_FILE = "FILES/config.json"  # Path to your config file

# Function to load the OWNER_ID from config file
def load_owner_id():
    try:
        with open(CONFIG_FILE, "r") as f:
            config_data = json.load(f)
            return config_data.get("OWNER")
    except FileNotFoundError:
        print("Config file not found.")
        return None

# Function to get IST time
def get_ist_time():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

# Load users from the JSON file
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save the updated users to the JSON file
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# Default plan data for new users
def default_plan(user_id):
    OWNER_ID = load_owner_id()

    if user_id == OWNER_ID:
        return {
            "plan": "Owner",
            "activated_at": get_ist_time(),
            "expires_at": None,
            "antispam": None,
            "mlimit": None,
            "credits": "∞",
            "badge": "🎭",
            "private": "on",
            "keyredeem": 0
        }

    return {
        "plan": "Free",
        "activated_at": get_ist_time(),
        "expires_at": None,
        "antispam": 15,
        "mlimit": 5,
        "credits": 100,
        "badge": "🧿",
        "private": "off",
        "keyredeem": 0
    }


# Handle the register callback (button press)
@Client.on_callback_query(filters.regex("register"))
async def register_callback(client, callback_query):
    users = load_users()
    user_id = str(callback_query.from_user.id)

    OWNER_ID = load_owner_id()

    if user_id in users:
        user_data = users[user_id]
        first_name = user_data['first_name']
        profile = f"<a href='tg://user?id={user_id}'>{first_name}</a> ({user_data['role']})"

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Home", callback_data="home"),
             InlineKeyboardButton("Exit", callback_data="exit")]
        ])

        await callback_query.message.reply_text(f"<pre>User {profile} You Are Already Registered</pre>", reply_markup=buttons)
        return

    first_name = callback_query.from_user.first_name
    username = callback_query.from_user.username if callback_query.from_user.username else None

    plan_data = default_plan(user_id)
    role = plan_data["plan"]

    users[user_id] = {
        "first_name": first_name,
        "username": username,
        "user_id": callback_query.from_user.id,
        "registered_at": get_ist_time(),
        "plan": plan_data,
        "role": role
    }

    save_users(users)

    user_data = users[user_id]
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Home", callback_data="home"),
         InlineKeyboardButton("Exit", callback_data="exit")]
    ])

    await callback_query.message.edit_text(f"""<pre>Registration Successfull ✔</pre>
╭━━━━━━━━━━
│● <b>Name</b> : <code>{first_name} [{user_data['plan']['badge']}]</code>
│● <b>UserID</b> : <code>{user_id}</code>
│● <b>Credits</b> : <code>{user_data['plan']['credits']}</code>
│● <b>Role</b> : <code>{user_data['role']}</code>
╰━━━━━━━━━━""", reply_markup=buttons)


# Handle the /register command
@Client.on_message(filters.command("register") & ~filters.edited)
async def register_command(client, message):
    users = load_users()
    user_id = str(message.from_user.id)

    OWNER_ID = load_owner_id()

    if user_id in users:
        user_data = users[user_id]
        first_name = user_data['first_name']
        profile = f"<a href='tg://user?id={user_id}'>{first_name}</a> ({user_data['role']})"

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("Home", callback_data="home"),
             InlineKeyboardButton("Exit", callback_data="exit")]
        ])

        # Reply to the original message if the user is already registered
        await client.send_message(
            chat_id=message.chat.id,
            text=f"<pre>User {profile} You Are Already Registered</pre>",
            reply_to_message_id=message.id,
            reply_markup=buttons
        )
        return

    first_name = message.from_user.first_name
    username = message.from_user.username if message.from_user.username else None

    plan_data = default_plan(user_id)
    role = plan_data["plan"]

    users[user_id] = {
        "first_name": first_name,
        "username": username,
        "user_id": message.from_user.id,
        "registered_at": get_ist_time(),
        "plan": plan_data,
        "role": role
    }

    save_users(users)

    user_data = users[user_id]
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Home", callback_data="home"),
         InlineKeyboardButton("Exit", callback_data="exit")]
    ])

    # Reply to the original message for successful registration
    await client.send_message(
        chat_id=message.chat.id,
        text=f"""<pre>Registration Successfull ✔</pre>
╭━━━━━━━━━━
│● <b>Name</b> : <code>{first_name} [{user_data['plan']['badge']}]</code>
│● <b>UserID</b> : <code>{user_id}</code>
│● <b>Credits</b> : <code>{user_data['plan']['credits']}</code>
│● <b>Role</b> : <code>{user_data['role']}</code>
╰━━━━━━━━━━""",
        reply_to_message_id=message.id,
        reply_markup=buttons
    )

@Client.on_message(filters.command("cmds") & ~filters.edited)
async def show_cmds(client, message):
    home_text = """<pre>JOIN BEFORE USING. ✔️</pre>
<b>~ Main :</b> <b><a href="https://t.me/Sosmain">Join Now</a></b>
<b>~ Chat Group :</b> <b><a href="https://t.me/Sosxchats">Join Now</a></b>
<b>~ Scrapper :</b> <b><a href="https://t.me/SoskeUI">Join Now</a></b>
<b>~ Note :</b> <code>Report Bugs To @sosblastbot</code>
<b>~ Proxy :</b> <code>Live 💎</code>
<pre>Choose Your Gate Type :</pre>"""

    home_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Gates", callback_data="gates"),
            InlineKeyboardButton("Tools", callback_data="tools")
        ],
        [
            InlineKeyboardButton("Close", callback_data="exit")
        ]
    ])

    await message.reply(
        home_text,
        reply_to_message_id=message.id,
        reply_markup=home_buttons,
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex("^(exit|close|home|gates|tools|auth|charge|shopify|auto|braintree|stripe)$"))
async def handle_callbacks(client, callback_query):
    data = callback_query.data

    if data in ["exit", "close"]:
        await callback_query.message.edit_text("<pre>Thanks For Using #Sos</pre>")

    elif data == "home":
        # Home text jab home button click kare
        home_text = """<pre>JOIN BEFORE USING. ✔️</pre>
<b>~ Main :</b> <b><a href="https://t.me/SosMain">Join Now</a></b>
<b>~ Chat Group :</b> <b><a href="https://t.me/SosxChats">Join Now</a></b>
<b>~ Scrapper :</b> <b><a href="https://t.me/SoskeUI">Join Now</a></b>
<b>~ Note :</b> <code>Report Bugs To @sosblastbot</code>
<b>~ Proxy :</b> <code>Live 💎</code>
<pre>Choose Your Gate Type :</pre>"""

        home_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Gates", callback_data="gates"),
                InlineKeyboardButton("Tools", callback_data="tools")
            ],
            [
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])

        await callback_query.message.edit_text(
            home_text,
            reply_markup=home_buttons,
            disable_web_page_preview=True
        )

    elif data == "gates":
        # Gates ke andar jaake buttons dikhao
        gates_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Auth", callback_data="auth"),
                InlineKeyboardButton("Charge", callback_data="charge")
            ],
            [
                InlineKeyboardButton("Back", callback_data="home")  # yaha se home jaayega
            ]
        ])

        gates_text = "<pre>Choose Gate Type:</pre>"

        await callback_query.message.edit_text(
            gates_text,
            reply_markup=gates_buttons
        )

    elif data == "auth":
        auth_text = """<pre>#Sos 〔AUTH GATES〕</pre>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>Name</b>: <code>Stripe Auth [NEW API]</code>
⟐ <b>Command</b>: <code>/au cc|mes|ano|cvv</code>
⟐ <b>Mass Cmd</b>: <code>/mau cc|mes|ano|cvv</code>
⟐ <b>Status</b>: <code>Active ✅</code>
⟐ <b>Note</b>: <code>Real Stripe Checking</code>
═══════════════════
⟐ <b>Name</b>: <code>AutoStripe [Site Based]</code>
⟐ <b>Command</b>: <code>/str cc|mes|ano|cvv</code>
⟐ <b>Mass Cmd</b>: <code>/mstr cc|mes|ano|cvv</code>
⟐ <b>Status</b>: <code>Active ✅</code>
⟐ <b>Note</b>: <code>Requires /addurl first</code>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>Name</b>: <code>Braintree Auth HQ</code>
⟐ <b>Command</b>: <code>$b3 cc|mes|ano|cvv</code>
⟐ <b>Status</b>: <code>Active ✅</code>
"""
        auth_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Back", callback_data="gates"),
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])
        await callback_query.message.edit_text(
            auth_text,
            reply_markup=auth_buttons
        )

    elif data == "charge":
        charge_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Shopify", callback_data="shopify"),
                InlineKeyboardButton("[AUTOSTRIPE]", callback_data="auto")
            ],
            [
                InlineKeyboardButton("Braintree", callback_data="braintree"),
                InlineKeyboardButton("Stripe", callback_data="stripe")
            ],
            [
                InlineKeyboardButton("Back", callback_data="gates"),
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])

        charge_text = "<pre>#Sos 〔 Charge 〕</pre>"

        await callback_query.message.edit_text(
            charge_text,
            reply_markup=charge_buttons
        )

    elif data == "shopify":
        shopify_text = """<pre>#Shopify 〔Charge〕</pre>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>Name</b>: <code>Shopify 1$</code>
⟐ <b>Command</b>: <code>$sho cc|mes|ano|cvv</code>
⟐ <b>Status: Dead ❌</b>

<pre>#Shopify 〔Charge〕</pre>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>Name</b>: <code>Shopify 1$</code>
⟐ <b>Command</b>: <code>$sg cc|mes|ano|cvv</code>
⟐ <b>Status: Dead ❌</b>
"""
        shopify_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Back", callback_data="charge"),
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])
        await callback_query.message.edit_text(
            shopify_text,
            reply_markup=shopify_buttons
        )

    elif data == "auto":
        auto_text = """<pre>#AutoStripe 〔Site Based〕</pre>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>/addurl</b>: <code>Add Site in Bot Private</code>
⟐ <b>/str</b>: <code>/str cc|mes|ano|cvv [Single]</code>
⟐ <b>/mstr</b>: <code>/mstr cc|mes|ano|cvv [Mass]</code>
⟐ <b>Status: Active ✅</b>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>/mysite</b>: <code>View your current site</code>
⟐ <b>/delsite</b>: <code>Remove your site</code>

<pre>#Stripe Auth 〔New API〕</pre>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>/au</b>: <code>/au cc|mes|ano|cvv [Single]</code>
⟐ <b>/mau</b>: <code>/mau cc|mes|ano|cvv [Mass]</code>
⟐ <b>Status: Active ✅</b>
⟐ <b>Note</b>: <code>No site needed, real API</code>
"""
        auto_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Back", callback_data="charge"),
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])
        await callback_query.message.edit_text(
            auto_text,
            reply_markup=auto_buttons
        )

    elif data == "stripe":
        stripe_text = """<pre>#Stripe 〔Charge〕</pre>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>Name</b>: <code>Stripe 1$</code>
⟐ <b>Command</b>: <code>$mag cc|mes|ano|cvv</code>
⟐ <b>Status: Active ✅</b>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
⟐ <b>Mass Cmd</b>: <code>$mmag cc|mes|ano|cvv</code>
⟐ <b>Limit</b>: <code>As Per User's Plan</code>
⟐ <b>Status: Active ✅</b>
"""
        stripe_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Back", callback_data="charge"),
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])
        await callback_query.message.edit_text(
            stripe_text,
            reply_markup=stripe_buttons
        )

    elif data in ["braintree"]:
        working_text = "<pre>Currently Working...!</pre>"

        working_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Back", callback_data="charge"),
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])
        await callback_query.message.edit_text(
            working_text,
            reply_markup=working_buttons
        )

    elif data == "tools":
        tools_text = """<pre>#Sos 〔TOOLS〕</pre>
━ ━ ━ ━ ━━━ ━ ━ ━ ━
<b>📇 BIN Tools:</b>
⟐ <code>/bin 414720</code> - BIN Lookup
⟐ <code>/mbin bins</code> - Mass BIN Lookup
⟐ <code>/vbv 414720</code> - Check VBV Status
⟐ <code>/mvbv bins</code> - Mass VBV Check
⟐ <code>/nonvbv 5</code> - Get Non-VBV Bins
━ ━ ━ ━ ━━━ ━ ━ ━ ━
<b>💳 Generator:</b>
⟐ <code>/gen 414720</code> - Generate 10 Cards
⟐ <code>/gen 414720 50</code> - Generate 50 Cards
━ ━ ━ ━ ━━━ ━ ━ ━ ━
<b>🧾 Fake Info:</b>
⟐ <code>/fake us</code> - Fake US Identity
⟐ <code>/fake uk</code> - Fake UK Identity
━ ━ ━ ━ ━━━ ━ ━ ━ ━
<b>🔗 Proxy Tools:</b>
⟐ <code>/rproxy 3</code> - Get Random Proxies
⟐ <code>/tproxy</code> - Test Random Proxy
⟐ <code>/proxyinfo</code> - Proxy Pool Info
⟐ <code>/setpx proxy</code> - Set Your Proxy
⟐ <code>/getpx</code> - Get Your Proxy
⟐ <code>/delpx</code> - Delete Your Proxy
━ ━ ━ ━ ━━━ ━ ━ ━ ━
<b>📝 Other:</b>
⟐ <code>/f</code> - Submit Feedback (Reply to Image)
⟐ <code>/info</code> - Your Account Info
⟐ <code>/redeem code</code> - Redeem Code
"""
        tools_buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Back", callback_data="home"),
                InlineKeyboardButton("Close", callback_data="exit")
            ]
        ])
        await callback_query.message.edit_text(
            tools_text,
            reply_markup=tools_buttons
        )
