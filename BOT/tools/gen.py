import os
import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from TOOLS.getbin import get_bin_details

def luhn(cc_base, length):
    cc = [int(x) for x in cc_base]
    while len(cc) < length - 1:
        cc.append(random.randint(0, 9))
    sum_ = sum(cc[::-2])
    for i in cc[-2::-2]:
        sum_ += sum([int(x) for x in str(i * 2)])
    check = (10 - sum_ % 10) % 10
    return ''.join(map(str, cc)) + str(check)

def fill_pattern(value, length, default_range):
    if not value:
        return str(random.randint(*default_range)).zfill(length)
    result = ""
    for ch in value:
        if ch.lower() == 'x':
            result += str(random.randint(0, 9))
        else:
            result += ch
    return result.zfill(length)[:length]

def generate_cards(bin_code, mes, ano, cvv, amount, brand=""):
    cards = []

    brand_lower = brand.lower()
    cvv_len = 4 if "amex" in brand_lower or "american express" in brand_lower else 3
    
    # Get current year for validation
    from datetime import datetime
    current_year = int(datetime.now().strftime("%y"))

    for _ in range(amount):

        cc_list = [str(random.randint(0, 9)) if ch.lower() == 'x' else ch for ch in bin_code]
        cc_number = ''.join(cc_list)[:15]
        cc_final = luhn(list(map(int, cc_number)), 16)

        mm = fill_pattern(mes, 2, (1, 12))
        # Generate year from current year + 1 to current year + 5 (valid cards)
        yy = fill_pattern(ano, 2, (current_year + 1, current_year + 5))
        cvv_ = fill_pattern(cvv, cvv_len, (10**(cvv_len-1), 10**cvv_len - 1))

        cards.append(f"{cc_final}|{mm}|{yy}|{cvv_}")
    return "\n".join(cards)

def code_block(ccs):
    return '\n'.join([f"<code>{x}</code>" for x in ccs.splitlines()])

async def handle_gen(client, message: Message, extrap, amount, edit_msg_id=None, reply_to=None):
    try:
        if len(extrap) < 6 or not extrap[:6].isdigit():
            return await message.reply("❌ Invalid BIN format. Use: 414720xxxxxxxxxx|xx|xx", quote=True)

        cc_parts = extrap.split("|")
        cc = cc_parts[0].ljust(16, "x")
        mes = cc_parts[1] if len(cc_parts) > 1 else None
        ano = cc_parts[2] if len(cc_parts) > 2 else None
        cvv = cc_parts[3] if len(cc_parts) > 3 else None

        bin_data = get_bin_details(cc[:6])
        if not bin_data:
            return await message.reply("❌ Invalid BIN or not found.", quote=True)

        brand = bin_data.get("vendor", "N/A")
        type_ = bin_data.get("type", "N/A")
        level = bin_data.get("level", "N/A")
        bank = bin_data.get("bank", "N/A")
        country = bin_data.get("country", "N/A")
        flag = bin_data.get("flag", "🏳")

        all_cards = generate_cards(cc, mes, ano, cvv, amount, brand)

        if amount > 10:
            os.makedirs("downloads", exist_ok=True)
            filename = f"downloads/{amount}_cards_{message.from_user.id}.txt"
            with open(filename, "w") as f:
                f.write(all_cards)

            await message.reply_document(
                filename,
                caption=(
                    f"• <b>Bin:</b> <code>{cc}</code></code>\n"
                    f"• <b>Amount:</b> <code>{amount}</code>\n"
                    f"• <b>Info:</b> <code>{brand} - {type_} - {level}</code>\n"
                    f"• <b>Bank:</b> <code>{bank}</code>\n"
                    f"• <b>Country:</b> <code>{country} {flag}</code>\n"
                    f"━━━━━━━━━━━━━"
                ),
                quote=True
            )
            os.remove(filename)
        else:
            text = (
                f"• <b>Bin:</b> <code>{cc}</code></code>\n"
                f"• <b>Amount:</b> <code>{amount}</code>\n\n"
                f"{code_block(all_cards)}\n"
                f"━━━━━━━━━━━━━\n"
                f"• <b>Info:</b> <code>{brand} - {type_} - {level}</code>\n"
                f"• <b>Bank:</b> <code>{bank}</code>\n"
                f"• <b>Country:</b> <code>{country} {flag}</code>"
            )
            buttons = InlineKeyboardMarkup([[
                InlineKeyboardButton("Regenerate", callback_data=f"regen|{cc}|{mes or ''}|{ano or ''}|{cvv or ''}|{amount}"),
                InlineKeyboardButton("Close", callback_data="close")
            ]])

            if edit_msg_id:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=edit_msg_id,
                    text=text,
                    reply_markup=buttons
                )
            else:
                await client.send_message(
                    chat_id=message.chat.id,
                    text=text,
                    reply_markup=buttons,
                    reply_to_message_id=reply_to or message.id
                )

    except Exception as e:
        await message.reply(f"❌ Error: <code>{str(e)}</code>", quote=True)

@Client.on_message(filters.command(["gen", ".gen", "$gen"]) & ~filters.edited)
async def gen_command(client, message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.reply("❌ Usage: /gen {bin/extrap} {amount (optional)}", quote=True)

    extrap = args[1]
    amount = int(args[2]) if len(args) > 2 and args[2].isdigit() else 10
    await handle_gen(client, message, extrap, amount, reply_to=message.id)

@Client.on_callback_query(filters.regex(r"^regen\|"))
async def regen_callback(client, callback):
    data = callback.data
    _, cc, mes, ano, cvv, amount = data.split("|")
    extrap = f"{cc}|{mes}|{ano}|{cvv}"
    await handle_gen(client, callback.message, extrap, int(amount), edit_msg_id=callback.message.id)

@Client.on_callback_query(filters.regex(r"^close$"))
async def close_callback(client, callback):
    try:
        await callback.message.delete()
    except:
        pass

