import json
import os
import random
import string
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from datetime import datetime
import pytz

USERS_FILE = "DATA/users.json"
CONFIG_FILE = "FILES/config.json"
REDEEM_FILE = "DATA/redeem_codes.json"

def get_owner_id():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return int(config.get("OWNER", 0))
    except:
        return 0

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    os.makedirs("DATA", exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_ist_time():
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

# Plan configurations
PLANS = {
    "plan1": {
        "plan": "Basic",
        "badge": "⭐",
        "credits": 500,
        "antispam": 10,
        "mlimit": 15,
        "private": "on"
    },
    "plan2": {
        "plan": "Standard",
        "badge": "💫",
        "credits": 1000,
        "antispam": 7,
        "mlimit": 25,
        "private": "on"
    },
    "plan3": {
        "plan": "Premium",
        "badge": "💎",
        "credits": 2500,
        "antispam": 5,
        "mlimit": 50,
        "private": "on"
    },
    "plan4": {
        "plan": "VIP",
        "badge": "👑",
        "credits": 5000,
        "antispam": 3,
        "mlimit": 100,
        "private": "on"
    },
    "plan5": {
        "plan": "Ultimate",
        "badge": "🎭",
        "credits": "∞",
        "antispam": None,
        "mlimit": None,
        "private": "on"
    }
}

@Client.on_message(filters.command("users"))
async def list_users(client: Client, message: Message):
    """List all registered users with their plans"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    users = load_users()
    
    if not users:
        return await message.reply("<pre>No Users Found</pre>", parse_mode=ParseMode.HTML)
    
    text = "<pre>Registered Users ~ Sos ✦</pre>\n━━━━━━━━━━━━━━━\n\n"
    
    count = 0
    for user_id, data in users.items():
        count += 1
        name = data.get("first_name", "Unknown")
        plan_data = data.get("plan", {})
        plan_name = plan_data.get("plan", "Free")
        badge = plan_data.get("badge", "🎟️")
        credits = plan_data.get("credits", 0)
        
        text += f"<b>{count}.</b> {name} {badge}\n"
        text += f"   • ID: <code>{user_id}</code>\n"
        text += f"   • Plan: <code>{plan_name}</code>\n"
        text += f"   • Credits: <code>{credits}</code>\n\n"
        
        # Limit to 20 users per message
        if count >= 20:
            text += f"\n<i>... and {len(users) - 20} more users</i>"
            break
    
    text += f"━━━━━━━━━━━━━━━\n<b>Total Users:</b> {len(users)}"
    
    await message.reply(text, parse_mode=ParseMode.HTML)


@Client.on_message(filters.command(["plan1", "plan2", "plan3", "plan4", "plan5"]))
async def give_plan(client: Client, message: Message):
    """Give plan to a user"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    plan_cmd = message.command[0].lower()  # plan1, plan2, etc.
    
    if plan_cmd not in PLANS:
        return await message.reply("❌ Invalid plan.")
    
    # Get target user
    target_id = None
    
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        target = message.command[1]
        # Check if it's a username or ID
        if target.startswith("@"):
            # It's a username, need to find user
            users = load_users()
            for uid, data in users.items():
                if data.get("username", "").lower() == target[1:].lower():
                    target_id = uid
                    target_name = data.get("first_name", "Unknown")
                    break
            if not target_id:
                return await message.reply(f"❌ User {target} not found.")
        else:
            target_id = target
            users = load_users()
            if target_id in users:
                target_name = users[target_id].get("first_name", "Unknown")
            else:
                return await message.reply(f"❌ User ID {target_id} not found.")
    else:
        return await message.reply(
            f"❌ Usage:\n"
            f"• Reply to user: <code>/{plan_cmd}</code>\n"
            f"• By ID: <code>/{plan_cmd} 123456789</code>\n"
            f"• By username: <code>/{plan_cmd} @username</code>",
            parse_mode=ParseMode.HTML
        )
    
    users = load_users()
    
    if target_id not in users:
        return await message.reply(f"❌ User {target_id} is not registered.")
    
    # Apply plan
    plan_config = PLANS[plan_cmd]
    users[target_id]["plan"] = {
        "plan": plan_config["plan"],
        "badge": plan_config["badge"],
        "credits": plan_config["credits"],
        "antispam": plan_config["antispam"],
        "mlimit": plan_config["mlimit"],
        "private": plan_config["private"],
        "activated_at": get_ist_time(),
        "expires_at": None,
        "keyredeem": users[target_id].get("plan", {}).get("keyredeem", 0)
    }
    users[target_id]["role"] = plan_config["plan"]
    
    save_users(users)
    
    await message.reply(
        f"<pre>Plan Assigned ✅</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] User:</b> {target_name}\n"
        f"<b>[•] ID:</b> <code>{target_id}</code>\n"
        f"<b>[•] Plan:</b> <code>{plan_config['plan']} {plan_config['badge']}</code>\n"
        f"<b>[•] Credits:</b> <code>{plan_config['credits']}</code>\n"
        f"<b>[•] Antispam:</b> <code>{plan_config['antispam']}s</code>\n"
        f"<b>[•] Mass Limit:</b> <code>{plan_config['mlimit']}</code>\n"
        f"━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.command("rmvplan"))
async def remove_plan(client: Client, message: Message):
    """Remove plan from user (reset to Free)"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    # Get target user
    target_id = None
    
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        target = message.command[1]
        if target.startswith("@"):
            users = load_users()
            for uid, data in users.items():
                if data.get("username", "").lower() == target[1:].lower():
                    target_id = uid
                    target_name = data.get("first_name", "Unknown")
                    break
            if not target_id:
                return await message.reply(f"❌ User {target} not found.")
        else:
            target_id = target
            users = load_users()
            if target_id in users:
                target_name = users[target_id].get("first_name", "Unknown")
            else:
                return await message.reply(f"❌ User ID {target_id} not found.")
    else:
        return await message.reply(
            "❌ Usage:\n"
            "• Reply to user: <code>/rmvplan</code>\n"
            "• By ID: <code>/rmvplan 123456789</code>\n"
            "• By username: <code>/rmvplan @username</code>",
            parse_mode=ParseMode.HTML
        )
    
    users = load_users()
    
    if target_id not in users:
        return await message.reply(f"❌ User {target_id} is not registered.")
    
    # Reset to Free plan
    users[target_id]["plan"] = {
        "plan": "Free",
        "badge": "🧿",
        "credits": 100,
        "antispam": 15,
        "mlimit": 5,
        "private": "off",
        "activated_at": get_ist_time(),
        "expires_at": None,
        "keyredeem": 0
    }
    users[target_id]["role"] = "Free"
    
    save_users(users)
    
    await message.reply(
        f"<pre>Plan Removed ✅</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] User:</b> {target_name}\n"
        f"<b>[•] ID:</b> <code>{target_id}</code>\n"
        f"<b>[•] Plan:</b> <code>Free 🧿</code>\n"
        f"<b>[•] Credits:</b> <code>100</code>\n"
        f"━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.command("addcredits"))
async def add_credits(client: Client, message: Message):
    """Add credits to a user"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    # Get target and amount
    if len(message.command) < 2:
        return await message.reply(
            "❌ Usage:\n"
            "• Reply: <code>/addcredits 500</code>\n"
            "• By ID: <code>/addcredits 123456789 500</code>",
            parse_mode=ParseMode.HTML
        )
    
    target_id = None
    amount = 0
    
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
        target_name = message.reply_to_message.from_user.first_name
        try:
            amount = int(message.command[1])
        except:
            return await message.reply("❌ Invalid amount.")
    elif len(message.command) >= 3:
        target_id = message.command[1]
        try:
            amount = int(message.command[2])
        except:
            return await message.reply("❌ Invalid amount.")
        users = load_users()
        if target_id in users:
            target_name = users[target_id].get("first_name", "Unknown")
        else:
            return await message.reply(f"❌ User {target_id} not found.")
    else:
        return await message.reply("❌ Please provide user and amount.")
    
    users = load_users()
    
    if target_id not in users:
        return await message.reply(f"❌ User {target_id} is not registered.")
    
    current_credits = users[target_id].get("plan", {}).get("credits", 0)
    
    if current_credits == "∞":
        return await message.reply("❌ User has infinite credits.")
    
    new_credits = int(current_credits) + amount
    users[target_id]["plan"]["credits"] = str(new_credits)
    
    save_users(users)
    
    await message.reply(
        f"<pre>Credits Added ✅</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] User:</b> {target_name}\n"
        f"<b>[•] Added:</b> <code>+{amount}</code>\n"
        f"<b>[•] New Balance:</b> <code>{new_credits}</code>\n"
        f"━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )




def load_redeem_codes():
    try:
        with open(REDEEM_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_redeem_codes(codes):
    os.makedirs("DATA", exist_ok=True)
    with open(REDEEM_FILE, "w") as f:
        json.dump(codes, f, indent=4)

def generate_code(length=12):
    """Generate random redeem code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


@Client.on_message(filters.command("red"))
async def generate_redeem_codes(client: Client, message: Message):
    """Generate redeem codes: /red quantity credits"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    if len(message.command) < 3:
        return await message.reply(
            "❌ Usage: <code>/red quantity credits</code>\n"
            "Example: <code>/red 5 500</code> (5 codes with 500 credits each)",
            parse_mode=ParseMode.HTML
        )
    
    try:
        quantity = int(message.command[1])
        credits = int(message.command[2])
    except:
        return await message.reply("❌ Invalid quantity or credits.")
    
    if quantity < 1 or quantity > 50:
        return await message.reply("❌ Quantity must be between 1-50.")
    
    if credits < 1:
        return await message.reply("❌ Credits must be at least 1.")
    
    codes = load_redeem_codes()
    generated = []
    
    for _ in range(quantity):
        code = generate_code()
        while code in codes:
            code = generate_code()
        
        codes[code] = {
            "credits": credits,
            "created_at": get_ist_time(),
            "created_by": message.from_user.id,
            "used": False,
            "used_by": None
        }
        generated.append(code)
    
    save_redeem_codes(codes)
    
    codes_text = "\n".join([f"<code>{c}</code>" for c in generated])
    
    await message.reply(
        f"<pre>Redeem Codes Generated ✅</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] Quantity:</b> <code>{quantity}</code>\n"
        f"<b>[•] Credits:</b> <code>{credits}</code> each\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>Codes:</b>\n{codes_text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>Usage:</b> <code>/redeem CODE</code>",
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.command("redeem"))
async def redeem_code(client: Client, message: Message):
    """Redeem a code for credits"""
    if len(message.command) < 2:
        return await message.reply(
            "❌ Usage: <code>/redeem CODE</code>",
            parse_mode=ParseMode.HTML
        )
    
    code = message.command[1].upper()
    user_id = str(message.from_user.id)
    
    users = load_users()
    
    if user_id not in users:
        return await message.reply("❌ You need to /register first.")
    
    codes = load_redeem_codes()
    
    if code not in codes:
        return await message.reply("❌ Invalid redeem code.")
    
    if codes[code]["used"]:
        return await message.reply("❌ This code has already been used.")
    
    credits_to_add = codes[code]["credits"]
    
    # Mark code as used
    codes[code]["used"] = True
    codes[code]["used_by"] = user_id
    codes[code]["used_at"] = get_ist_time()
    save_redeem_codes(codes)
    
    # Add credits to user
    current_credits = users[user_id].get("plan", {}).get("credits", 0)
    
    if current_credits == "∞":
        return await message.reply("❌ You already have infinite credits!")
    
    new_credits = int(current_credits) + credits_to_add
    users[user_id]["plan"]["credits"] = str(new_credits)
    users[user_id]["plan"]["keyredeem"] = users[user_id].get("plan", {}).get("keyredeem", 0) + 1
    save_users(users)
    
    await message.reply(
        f"<pre>Code Redeemed ✅</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] Code:</b> <code>{code}</code>\n"
        f"<b>[•] Credits Added:</b> <code>+{credits_to_add}</code>\n"
        f"<b>[•] New Balance:</b> <code>{new_credits}</code>\n"
        f"━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.command("codes"))
async def list_codes(client: Client, message: Message):
    """List all redeem codes (owner only)"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    codes = load_redeem_codes()
    
    if not codes:
        return await message.reply("<pre>No Redeem Codes</pre>", parse_mode=ParseMode.HTML)
    
    unused = [c for c, d in codes.items() if not d["used"]]
    used = [c for c, d in codes.items() if d["used"]]
    
    text = "<pre>Redeem Codes ~ Sos ✦</pre>\n━━━━━━━━━━━━━━━\n\n"
    
    if unused:
        text += "<b>🟢 Unused Codes:</b>\n"
        for code in unused[:15]:
            credits = codes[code]["credits"]
            text += f"• <code>{code}</code> ({credits} credits)\n"
        if len(unused) > 15:
            text += f"<i>... and {len(unused)-15} more</i>\n"
    
    text += f"\n<b>Total Unused:</b> {len(unused)}\n"
    text += f"<b>Total Used:</b> {len(used)}"
    
    await message.reply(text, parse_mode=ParseMode.HTML)


@Client.on_message(filters.command("rmvcred"))
async def remove_credits(client: Client, message: Message):
    """Remove all credits from a user"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    # Get target user
    target_id = None
    
    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        target = message.command[1]
        if target.startswith("@"):
            users = load_users()
            for uid, data in users.items():
                if data.get("username", "").lower() == target[1:].lower():
                    target_id = uid
                    target_name = data.get("first_name", "Unknown")
                    break
            if not target_id:
                return await message.reply(f"❌ User {target} not found.")
        else:
            target_id = target
            users = load_users()
            if target_id in users:
                target_name = users[target_id].get("first_name", "Unknown")
            else:
                return await message.reply(f"❌ User ID {target_id} not found.")
    else:
        return await message.reply(
            "❌ Usage:\n"
            "• Reply to user: <code>/rmvcred</code>\n"
            "• By ID: <code>/rmvcred 123456789</code>\n"
            "• By username: <code>/rmvcred @username</code>",
            parse_mode=ParseMode.HTML
        )
    
    users = load_users()
    
    if target_id not in users:
        return await message.reply(f"❌ User {target_id} is not registered.")
    
    old_credits = users[target_id].get("plan", {}).get("credits", 0)
    users[target_id]["plan"]["credits"] = "0"
    
    save_users(users)
    
    await message.reply(
        f"<pre>Credits Removed ✅</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] User:</b> {target_name}\n"
        f"<b>[•] ID:</b> <code>{target_id}</code>\n"
        f"<b>[•] Old Credits:</b> <code>{old_credits}</code>\n"
        f"<b>[•] New Credits:</b> <code>0</code>\n"
        f"━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.command("delcode"))
async def delete_code(client: Client, message: Message):
    """Delete a redeem code"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    if len(message.command) < 2:
        return await message.reply(
            "❌ Usage: <code>/delcode CODE</code>",
            parse_mode=ParseMode.HTML
        )
    
    code = message.command[1].upper()
    codes = load_redeem_codes()
    
    if code not in codes:
        return await message.reply("❌ Code not found.")
    
    del codes[code]
    save_redeem_codes(codes)
    
    await message.reply(f"✅ Code <code>{code}</code> deleted.", parse_mode=ParseMode.HTML)


@Client.on_message(filters.command("clearused"))
async def clear_used_codes(client: Client, message: Message):
    """Clear all used redeem codes"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    codes = load_redeem_codes()
    
    unused = {c: d for c, d in codes.items() if not d["used"]}
    removed = len(codes) - len(unused)
    
    save_redeem_codes(unused)
    
    await message.reply(
        f"✅ Cleared {removed} used codes.\n"
        f"Remaining: {len(unused)} unused codes.",
        parse_mode=ParseMode.HTML
    )
