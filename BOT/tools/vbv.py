from pyrogram import Client, filters
from pyrogram.types import Message
import os
import re

VBV_FILE = "FILES/vbvbin.txt"

def load_vbv_data():
    """Load VBV BIN data from file into a dictionary"""
    vbv_data = {}
    if not os.path.exists(VBV_FILE):
        return vbv_data
    
    with open(VBV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|")
            if len(parts) >= 3:
                bin_number = parts[0].strip()
                status = parts[1].strip()
                message = parts[2].strip()
                vbv_data[bin_number] = {
                    "status": status,
                    "message": message
                }
    return vbv_data

VBV_DATA = load_vbv_data()

def check_vbv(bin_number: str) -> dict:
    """Check if a BIN is VBV or Non-VBV"""
    bin_6 = bin_number[:6]
    if bin_6 in VBV_DATA:
        return VBV_DATA[bin_6]
    return None

@Client.on_message(filters.command("vbv") & ~filters.edited)
async def vbv_lookup(client, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "<b>Usage:</b> <code>/vbv {bin}</code>\n"
            "<b>Example:</b> <code>/vbv 414720</code>",
            reply_to_message_id=message.id
        )
    
    bin_input = ''.join(filter(str.isdigit, message.command[1]))
    if len(bin_input) < 6:
        return await message.reply(
            "<b>Invalid BIN ❌</b>\n<code>Must be at least 6 digits.</code>",
            reply_to_message_id=message.id
        )
    
    bin_number = bin_input[:6]
    vbv_info = check_vbv(bin_number)
    
    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"
    
    if not vbv_info:
        return await message.reply(
            f"<pre>VBV Check Result 🔍</pre>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>⊙ Bin:</b> <code>{bin_number}</code>\n"
            f"<b>⊙ Status:</b> <code>Not Found In Database</code>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<b>Checked By:</b> {profile}",
            reply_to_message_id=message.id
        )
    
    is_vbv = "TRUE" in vbv_info["status"].upper()
    status_emoji = "❌" if is_vbv else "✅"
    vbv_text = "VBV (3D Secure)" if is_vbv else "Non-VBV"
    
    reply_text = f"""<pre>VBV Check Result 🔍</pre>
━━━━━━━━━━━━━━━
<b>⊙ Bin:</b> <code>{bin_number}</code>
<b>⊙ VBV Status:</b> <code>{vbv_text}</code> {status_emoji}
<b>⊙ 3D Secure:</b> <code>{vbv_info['status']}</code>
<b>⊙ Message:</b> <code>{vbv_info['message']}</code>
━━━━━━━━━━━━━━━
<b>Checked By:</b> {profile}"""
    
    await message.reply(reply_text, reply_to_message_id=message.id)

@Client.on_message(filters.command("mvbv") & ~filters.edited)
async def mass_vbv_lookup(client, message: Message):
    if len(message.command) < 2:
        return await message.reply(
            "<b>Usage:</b> <code>/mvbv {bins}</code>\n"
            "<b>Example:</b> <code>/mvbv 414720 400047 400005</code>",
            reply_to_message_id=message.id
        )
    
    raw_input = message.text.split(None, 1)[1]
    candidates = re.findall(r'\b\d{6,16}\b', raw_input)
    bin_list = list({x[:6] for x in candidates if len(x) >= 6})
    
    if not bin_list:
        return await message.reply(
            "<b>No valid BINs found ❌</b>\n<code>Each BIN must be at least 6 digits.</code>",
            reply_to_message_id=message.id
        )
    
    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"
    
    results = []
    vbv_count = 0
    non_vbv_count = 0
    not_found_count = 0
    
    for bin_number in bin_list[:20]:  # Limit to 20
        vbv_info = check_vbv(bin_number)
        
        if not vbv_info:
            not_found_count += 1
            results.append(f"<b>⊙ Bin:</b> <code>{bin_number}</code> | <code>Not Found</code> ⚪")
            continue
        
        is_vbv = "TRUE" in vbv_info["status"].upper()
        if is_vbv:
            vbv_count += 1
            results.append(f"<b>⊙ Bin:</b> <code>{bin_number}</code> | <code>VBV</code> ❌")
        else:
            non_vbv_count += 1
            results.append(f"<b>⊙ Bin:</b> <code>{bin_number}</code> | <code>Non-VBV</code> ✅")
    
    summary = f"<b>✅ Non-VBV:</b> {non_vbv_count} | <b>❌ VBV:</b> {vbv_count} | <b>⚪ N/A:</b> {not_found_count}"
    
    reply_text = f"""<pre>Mass VBV Check Result 🔍</pre>
━━━━━━━━━━━━━━━
{chr(10).join(results)}
━━━━━━━━━━━━━━━
{summary}
<b>Checked By:</b> {profile}"""
    
    await message.reply(reply_text, reply_to_message_id=message.id, disable_web_page_preview=True)

@Client.on_message(filters.command("nonvbv") & ~filters.edited)
async def get_nonvbv_bins(client, message: Message):
    """Get random non-VBV bins from the database"""
    try:
        amount = int(message.command[1]) if len(message.command) > 1 else 5
        amount = min(amount, 25)  # Limit to 25
    except:
        amount = 5
    
    non_vbv_bins = [
        bin_num for bin_num, info in VBV_DATA.items()
        if "FALSE" in info["status"].upper()
    ]
    
    if not non_vbv_bins:
        return await message.reply(
            "<b>No Non-VBV bins found in database ❌</b>",
            reply_to_message_id=message.id
        )
    
    import random
    selected = random.sample(non_vbv_bins, min(amount, len(non_vbv_bins)))
    
    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"
    
    bin_list = "\n".join([f"<code>{b}</code>" for b in selected])
    
    reply_text = f"""<pre>Non-VBV Bins 🔍</pre>
━━━━━━━━━━━━━━━
{bin_list}
━━━━━━━━━━━━━━━
<b>Amount:</b> {len(selected)}
<b>Requested By:</b> {profile}"""
    
    await message.reply(reply_text, reply_to_message_id=message.id)
