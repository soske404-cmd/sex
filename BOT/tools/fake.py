from pyrogram import Client, filters
from pyrogram.types import Message
import requests

# Map common shorthand country codes to API codes
COUNTRY_CODE_MAP = {
    "uk": "gb",   # United Kingdom
    "jp": "jp",   # Japan
    "it": "it",   # Italy
    "sp": "es",   # Spain
    "sg": "sg",   # Singapore
    "us": "us",   # United States
    "ca": "ca",   # Canada
    "au": "au",   # Australia
    "de": "de",   # Germany
    "fr": "fr",   # France
    "in": "in",   # India
    "br": "br",   # Brazil
    "mx": "mx",   # Mexico
    "nl": "nl",   # Netherlands
    "ch": "ch",   # Switzerland
    "tr": "tr",   # Turkey
    "dk": "dk",   # Denmark
    "fi": "fi",   # Finland
    "no": "no",   # Norway
    "nz": "nz",   # New Zealand
    "ie": "ie",   # Ireland
}

@Client.on_message(filters.command("fake") & ~filters.edited)
async def generate_fake_user(client, message: Message):
    args = message.text.split()
    country_input = args[1].lower() if len(args) > 1 else "us"
    
    # Map shorthand to proper country code
    country_code = COUNTRY_CODE_MAP.get(country_input, country_input)

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
