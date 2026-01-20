from pyrogram import Client, filters
from TOOLS.getbin import get_bin_details
import re

@Client.on_message(filters.command("bin") & ~filters.edited)
async def bin_lookup(client, message):
    if len(message.command) < 2:
        return await message.reply("Please provide a BIN or card number.", reply_to_message_id=message.id)

    bin_input = ''.join(filter(str.isdigit, message.command[1]))
    if len(bin_input) < 6:
        return await message.reply("Invalid BIN. Must be at least 6 digits.", reply_to_message_id=message.id)

    bin_number = bin_input[:6]
    data = get_bin_details(bin_number)

    if not data:
        return await message.reply("No info found for this BIN.", reply_to_message_id=message.id)

    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"

    reply_text = f"""𝐁𝐢𝐧 𝐋𝐨𝐨𝐤𝐮𝐩 𝐑𝐞𝐬𝐮𝐥𝐭 🔍
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
𝐁𝐢𝐧 ➜ <code>{data['bin']}</code>
𝗜𝗻𝗳𝗼 ➜ <code>{data['vendor']}-{data['type']}-{data['level'] or "Unknown"}</code>
𝗜𝘀𝘀𝘂𝗲𝗿 ➜ <code>{data['bank']}</code> 🏛
𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➜ <code>{data['country']} {data['flag']}</code>
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 ➜ {profile}
"""

    await client.send_message(
        chat_id=message.chat.id,
        text=reply_text,
        reply_to_message_id=message.id,
        disable_web_page_preview=True
    )

@Client.on_message(filters.command("mbin") & ~filters.edited)
async def mass_bin_lookup(client, message):
    if len(message.command) < 2:
        return await message.reply("Please provide one or more BINs or card numbers.", reply_to_message_id=message.id)

    raw_input = message.text.split(None, 1)[1]

    # Extract 16+ digit card numbers or standalone BINs or BINs from cc|mm|yy|cvv formats
    candidates = re.findall(r'\b\d{6,16}\b', raw_input)
    bin_list = list({x[:6] for x in candidates if len(x) >= 6})

    if not bin_list:
        return await message.reply("No valid BINs found. Each BIN must be at least 6 digits.", reply_to_message_id=message.id)

    user_name = message.from_user.first_name
    profile = f"<a href='tg://user?id={message.from_user.id}'>{user_name}</a>"

    results = []
    for bin_number in bin_list[:20]:  # Optional limit to 20
        data = get_bin_details(bin_number)
        if not data:
            results.append(f"""𝐁𝐢𝐧 ➜ <code>{bin_number}</code>\n𝗦𝘁𝗮𝘁𝘂𝘀 ➜ <code>Not Found ❌</code>\n━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━""")
            continue

        results.append(f"""𝐁𝐢𝐧 𝐋𝐨𝐨𝐤𝐮𝐩 𝐑𝐞𝐬𝐮𝐥𝐭 🔍
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
𝐁𝐢𝐧 ➜ <code>{data['bin']}</code>
𝗜𝗻𝗳𝗼 ➜ <code>{data['vendor']}-{data['type']}-{data['level'] or "Unknown"}</code>
𝗜𝘀𝘀𝘂𝗲𝗿 ➜ <code>{data['bank']}</code> 🏛
𝗖𝗼𝘂𝗻𝘁𝗿𝘆 ➜ <code>{data['country']} {data['flag']}</code>
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━""")

    reply_text = "\n".join(results) + f"\n𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆 ➜ {profile}"

    await client.send_message(
        chat_id=message.chat.id,
        text=reply_text,
        reply_to_message_id=message.id,
        disable_web_page_preview=True
    )