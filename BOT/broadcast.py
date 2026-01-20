import json
import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

USERS_FILE = "DATA/users.json"
CONFIG_FILE = "FILES/config.json"

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


@Client.on_message(filters.command("broad") & filters.private)
async def broadcast_message(client: Client, message: Message):
    """Broadcast message to all users (Owner only)"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    # Get the message to broadcast
    broadcast_msg = None
    
    if message.reply_to_message:
        broadcast_msg = message.reply_to_message
    elif len(message.text.split(maxsplit=1)) > 1:
        text = message.text.split(maxsplit=1)[1]
        broadcast_msg = text
    else:
        return await message.reply(
            "❌ Usage:\n"
            "• Reply to a message: <code>/broad</code>\n"
            "• Or: <code>/broad Your message here</code>",
            parse_mode=ParseMode.HTML
        )
    
    users = load_users()
    
    if not users:
        return await message.reply("❌ No users to broadcast to.")
    
    status_msg = await message.reply(
        f"<pre>Broadcasting...</pre>\n"
        f"<b>Total Users:</b> {len(users)}",
        parse_mode=ParseMode.HTML
    )
    
    success = 0
    failed = 0
    
    for user_id in users.keys():
        try:
            if isinstance(broadcast_msg, str):
                await client.send_message(
                    int(user_id),
                    f"<pre>📢 Broadcast ~ Sos ✦</pre>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"{broadcast_msg}",
                    parse_mode=ParseMode.HTML
                )
            else:
                await broadcast_msg.copy(int(user_id))
            success += 1
        except Exception as e:
            failed += 1
        
        await asyncio.sleep(0.1)  # Avoid flood
    
    await status_msg.edit(
        f"<pre>Broadcast Complete ✅</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] Success:</b> <code>{success}</code>\n"
        f"<b>[•] Failed:</b> <code>{failed}</code>\n"
        f"<b>[•] Total:</b> <code>{len(users)}</code>",
        parse_mode=ParseMode.HTML
    )


@Client.on_message(filters.command("report"))
async def report_to_admin(client: Client, message: Message):
    """Report a message/issue to admin"""
    owner_id = get_owner_id()
    
    if not owner_id:
        return await message.reply("❌ Admin not configured.")
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "None"
    
    # Get report content
    report_content = None
    
    if message.reply_to_message:
        report_content = message.reply_to_message
    elif len(message.text.split(maxsplit=1)) > 1:
        report_content = message.text.split(maxsplit=1)[1]
    else:
        return await message.reply(
            "❌ Usage:\n"
            "• Reply to a message: <code>/report</code>\n"
            "• Or: <code>/report Your report message</code>",
            parse_mode=ParseMode.HTML
        )
    
    try:
        # Send report to admin
        report_header = (
            f"<pre>📩 New Report ~ Sos ✦</pre>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>[•] From:</b> {user_name}\n"
            f"<b>[•] ID:</b> <code>{user_id}</code>\n"
            f"<b>[•] Username:</b> {username}\n"
            f"━━━━━━━━━━━━━━━\n"
        )
        
        if isinstance(report_content, str):
            await client.send_message(
                owner_id,
                f"{report_header}<b>Message:</b>\n{report_content}",
                parse_mode=ParseMode.HTML
            )
        else:
            await client.send_message(
                owner_id,
                report_header,
                parse_mode=ParseMode.HTML
            )
            await report_content.copy(owner_id)
        
        await message.reply(
            "<pre>Report Sent ✅</pre>\n"
            "<b>Your report has been sent to the admin.</b>",
            parse_mode=ParseMode.HTML
        )
    
    except Exception as e:
        await message.reply(
            "<pre>Report Failed ❌</pre>\n"
            "<b>Could not send report to admin.</b>",
            parse_mode=ParseMode.HTML
        )


@Client.on_message(filters.command("reply") & filters.private)
async def reply_to_user(client: Client, message: Message):
    """Reply to a user from admin (Owner only)"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return await message.reply("❌ Only owner can use this command.")
    
    if len(message.command) < 3:
        return await message.reply(
            "❌ Usage: <code>/reply user_id Your message</code>",
            parse_mode=ParseMode.HTML
        )
    
    try:
        target_id = int(message.command[1])
        reply_text = " ".join(message.command[2:])
        
        await client.send_message(
            target_id,
            f"<pre>📬 Admin Reply ~ Sos ✦</pre>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{reply_text}",
            parse_mode=ParseMode.HTML
        )
        
        await message.reply(f"✅ Message sent to <code>{target_id}</code>", parse_mode=ParseMode.HTML)
    
    except Exception as e:
        await message.reply(f"❌ Failed: {e}")
