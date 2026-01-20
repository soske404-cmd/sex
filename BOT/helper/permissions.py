from pyrogram import Client, filters
from BOT.helper.start import load_users
from pyrogram.types import Message
import json
import os
from pyrogram.enums import ChatType

GROUPS_FILE = "DATA/groups.json"
CONFIG_FILE = "FILES/config.json"

def get_owner_id():
    """Get owner ID from config file"""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return int(config.get("OWNER", 0))
    except:
        return 0

def load_allowed_groups():
    if not os.path.exists(GROUPS_FILE):
        return []
    try:
        with open(GROUPS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_allowed_groups(groups):
    os.makedirs("DATA", exist_ok=True)
    with open(GROUPS_FILE, "w") as f:
        json.dump(groups, f, indent=4)

async def is_premium_user(message: Message) -> bool:
    try:
        db = load_users()
        user_id = str(message.from_user.id)

        user_data = db.get(user_id)
        if not user_data:
            await message.reply("❌ User not found in database.")
            return False

        user_plan = user_data.get("plan", {}).get("plan", "Free")
        if user_plan in ["Free", "Redeem Code"]:
            await message.reply_text(
                "<pre>Notification ❗️</pre>\n"
                "<b>~ Message :</b> <code>Only For Premium Users !</code>\n"
                '<b>~ Buy Premium →</b> <b><a href="t.me.gitsus">Click Here</a></b>\n'
                "━━━━━━━━━━━━━\n"
                "<b>Type <code>/buy</code> to get Premium.</b>",
                quote=True
            )
            return False

        return True
    except Exception as e:
        return False

async def check_private_access(message: Message) -> bool:
    try:
        allowed_groups = load_allowed_groups()
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if message.chat.id in allowed_groups:
                return True

        db = load_users()
        user_id = str(message.from_user.id)
        user_data = db.get(user_id)

        if not user_data:
            await message.reply("❌ User not found in database.")
            return False

        private_status = user_data.get("plan", {}).get("private", "off")
        if private_status != "on":
            await message.reply_text(
                "<pre>Notification ❗️</pre>\n"
                "<b>~ Message :</b> <code>Only For Premium Users !</code>\n"
                "<b>~ Use Free In Chat →</b> Click Here\n"
                "━━━━━━━━━━━━━\n"
                "<b>Type <code>/buy</code> to get Premium.</b>",
                quote=True
            )
            return False

        return True
    except Exception as e:
        return False

# Ensure groups file exists
if not os.path.exists(GROUPS_FILE):
    os.makedirs("DATA", exist_ok=True)
    with open(GROUPS_FILE, "w") as f:
        json.dump([], f)
