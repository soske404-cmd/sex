from pyrogram import Client, filters
from pyrogram.types import Message
import requests

@Client.on_message(filters.command("fake") & ~filters.edited)
async def generate_fake_user(client, message: Message):
    args = message.text.split()
    country_code = args[1].lower() if len(args) > 1 else "us"

    msg = await message.reply("<pre>Generating Fake Identity...</pre>", quote=True)

    try:
        response = requests.get(f"https://randomuser.me/api/?nat={country_code}")
        data = response.json()["results"][0]

        name = f"{data['name']['first']} {data['name']['last']}"
        gender = data['gender'].capitalize()
        street = f"{data['location']['street']['number']} {data['location']['street']['name']}"
        city = data['location']['city']
        state = data['location']['state']
        postcode = data['location']['postcode']
        country = data['location']['country']
        phone = data['phone']
        dob = data['dob']['date'][:10]

        reply_text = f"""
<b>⌥ [Fake Identity - {country_code.upper()}]</b> 🧾
━━━━━━━━━━━━━━━
<b>⊙ Name:</b> <code>{name}</code>
<b>⊙ Gender:</b> <code>{gender}</code>
<b>⊙ Street:</b> <code>{street}</code>
<b>⊙ City:</b> <code>{city}</code>
<b>⊙ State:</b> <code>{state}</code>
<b>⊙ Pincode:</b> <code>{postcode}</code>
<b>⊙ Country:</b> <code>{country}</code>
<b>⊙ Phone:</b> <code>{phone}</code>
<b>⊙ DOB:</b> <code>{dob}</code>
━━━━━━━━━━━━━━━
"""
        await msg.edit_text(reply_text)
    except Exception as e:
        await msg.edit_text("❌ Failed to fetch fake identity. Maybe invalid country code.")
