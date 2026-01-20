import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated
from pyrogram.enums import ChatMemberStatus, ChatType

GROUPS_FILE = "DATA/groups.json"
PENDING_FILE = "DATA/pending_groups.json"
CONFIG_FILE = "FILES/config.json"

def get_owner_id():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return int(config.get("OWNER", 0))
    except:
        return 0

def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []

def save_json(file_path, data):
    os.makedirs("DATA", exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_approved_groups():
    return load_json(GROUPS_FILE)

def load_pending_groups():
    return load_json(PENDING_FILE)

def save_approved_groups(groups):
    save_json(GROUPS_FILE, groups)

def save_pending_groups(groups):
    save_json(PENDING_FILE, groups)

# When bot is added to a group
@Client.on_chat_member_updated()
async def on_chat_member_updated(client: Client, chat_member: ChatMemberUpdated):
    """Detect when bot is added to a group"""
    try:
        # Check if this update is about the bot itself
        if chat_member.new_chat_member and chat_member.new_chat_member.user.is_self:
            # Bot was added to a group
            if chat_member.new_chat_member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]:
                chat = chat_member.chat
                owner_id = get_owner_id()
                
                if owner_id:
                    # Add to pending groups
                    pending = load_pending_groups()
                    approved = load_approved_groups()
                    
                    group_info = {
                        "id": chat.id,
                        "title": chat.title or "Unknown",
                        "username": chat.username or None
                    }
                    
                    # Check if already in approved or pending
                    if chat.id not in approved and not any(g.get("id") == chat.id for g in pending if isinstance(g, dict)):
                        # Add to pending if it's a dict list, else just add ID
                        if pending and isinstance(pending[0], dict):
                            pending.append(group_info)
                        else:
                            # Convert to new format
                            pending = [group_info]
                        save_pending_groups(pending)
                    
                    # Notify owner
                    status = "✅ Approved" if chat.id in approved else "⏳ Pending"
                    
                    await client.send_message(
                        owner_id,
                        f"<pre>Bot Added To Group 📥</pre>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"<b>[•] Title:</b> <code>{chat.title}</code>\n"
                        f"<b>[•] ID:</b> <code>{chat.id}</code>\n"
                        f"<b>[•] Username:</b> @{chat.username if chat.username else 'None'}\n"
                        f"<b>[•] Status:</b> {status}\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"<b>Use /add {chat.id} to approve</b>"
                    )
        
        # Bot was removed from group
        elif chat_member.old_chat_member and chat_member.old_chat_member.user.is_self:
            if chat_member.new_chat_member is None or chat_member.new_chat_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                chat = chat_member.chat
                owner_id = get_owner_id()
                
                if owner_id:
                    # Remove from pending
                    pending = load_pending_groups()
                    pending = [g for g in pending if (g.get("id") if isinstance(g, dict) else g) != chat.id]
                    save_pending_groups(pending)
                    
                    await client.send_message(
                        owner_id,
                        f"<pre>Bot Removed From Group 📤</pre>\n"
                        f"━━━━━━━━━━━━━━━\n"
                        f"<b>[•] Title:</b> <code>{chat.title}</code>\n"
                        f"<b>[•] ID:</b> <code>{chat.id}</code>"
                    )
    except Exception as e:
        pass

@Client.on_message(filters.command(["add", "addg"]))
async def add_group_cmd(client: Client, message: Message):
    """Approve a group"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return
    
    try:
        if len(message.command) < 2:
            if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                chat_id = message.chat.id
            else:
                return await message.reply("❌ Format: /add -100xxxx")
        else:
            chat_id = int(message.command[1])
        
        approved = load_approved_groups()
        pending = load_pending_groups()
        
        if chat_id in approved:
            return await message.reply(f"ℹ️ Group <code>{chat_id}</code> already approved.")
        
        approved.append(chat_id)
        save_approved_groups(approved)
        
        # Remove from pending
        pending = [g for g in pending if (g.get("id") if isinstance(g, dict) else g) != chat_id]
        save_pending_groups(pending)
        
        await message.reply(f"✅ Group <code>{chat_id}</code> approved!")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")

@Client.on_message(filters.command(["rmv", "rmvg"]))
async def remove_group_cmd(client: Client, message: Message):
    """Remove a group"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return
    
    try:
        if len(message.command) < 2:
            if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                chat_id = message.chat.id
            else:
                return await message.reply("❌ Format: /rmv -100xxxx")
        else:
            chat_id = int(message.command[1])
        
        approved = load_approved_groups()
        
        if chat_id not in approved:
            return await message.reply(f"ℹ️ Group <code>{chat_id}</code> not in approved list.")
        
        approved.remove(chat_id)
        save_approved_groups(approved)
        
        await message.reply(f"✅ Group <code>{chat_id}</code> removed!")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")

@Client.on_message(filters.command("groups"))
async def list_groups_cmd(client: Client, message: Message):
    """List all groups with status"""
    owner_id = get_owner_id()
    
    if message.from_user.id != owner_id:
        return
    
    approved = load_approved_groups()
    pending = load_pending_groups()
    
    text = "<pre>Groups List ~ Sos ✦</pre>\n━━━━━━━━━━━━━━━\n"
    
    # Approved groups
    if approved:
        text += "\n<b>✅ Approved Groups:</b>\n"
        for g in approved:
            text += f"• <code>{g}</code>\n"
    
    # Pending groups
    if pending:
        text += "\n<b>⏳ Pending Groups:</b>\n"
        for g in pending:
            if isinstance(g, dict):
                text += f"• <code>{g.get('id')}</code> - {g.get('title', 'Unknown')}\n"
            else:
                text += f"• <code>{g}</code>\n"
    
    if not approved and not pending:
        text += "\n<i>No groups found.</i>"
    
    text += f"\n━━━━━━━━━━━━━━━\n<b>Total Approved:</b> {len(approved)}\n<b>Total Pending:</b> {len(pending)}"
    
    await message.reply(text)
