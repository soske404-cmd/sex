
# import json
# import asyncio
# from pyrogram import Client, idle
# from BOT.plans.plan1 import check_and_expire_plans as plan1_expiry
# from BOT.plans.plan2 import check_and_expire_plans as plan2_expiry
# from BOT.plans.plan3 import check_and_expire_plans as plan3_expiry
# from BOT.plans.plan4 import check_and_expire_plans as plan4_expiry
# from BOT.plans.redeem import check_and_expire_redeem_plans as redeem_expiry

# # Load bot credentials
# with open("FILES/config.json", "r", encoding="utf-8") as f:
#     DATA = json.load(f)
#     API_ID = DATA["API_ID"]
#     API_HASH = DATA["API_HASH"]
#     BOT_TOKEN = DATA["BOT_TOKEN"]

# # Plugin directory
# plugins = dict(root="BOT")

# # Create bot instance
# bot = Client(
#     "MY_BOT",
#     api_id=API_ID,
#     api_hash=API_HASH,
#     bot_token=BOT_TOKEN,
#     plugins=plugins
# )

# async def main():
#     await bot.start()
#     print("✅ Bot is running...")

#     # Start background tasks for all plans
#     asyncio.create_task(plan1_expiry(bot))
#     asyncio.create_task(plan2_expiry(bot))
#     asyncio.create_task(plan3_expiry(bot))
#     asyncio.create_task(plan4_expiry(bot))
#     asyncio.create_task(redeem_expiry(bot))

#     await idle()
#     await bot.stop()
#     print("❌ Bot stopped.")

# if __name__ == "__main__":
#     import nest_asyncio
#     nest_asyncio.apply()
#     asyncio.run(main())


import json
import asyncio
import threading
from pyrogram import Client, idle
from flask import Flask
from BOT.plans.plan1 import check_and_expire_plans as plan1_expiry
from BOT.plans.plan2 import check_and_expire_plans as plan2_expiry
from BOT.plans.plan3 import check_and_expire_plans as plan3_expiry
from BOT.plans.plan4 import check_and_expire_plans as plan4_expiry
from BOT.plans.plan5 import check_and_expire_plans as plan5_expiry
from BOT.plans.redeem import check_and_expire_redeem_plans as redeem_expiry

# Load bot credentials
with open("FILES/config.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)
    API_ID = DATA["API_ID"]
    API_HASH = DATA["API_HASH"]
    BOT_TOKEN = DATA["BOT_TOKEN"]

# Pyrogram plugins
plugins = dict(root="BOT")

# Pyrogram client
bot = Client(
    "MY_BOT",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=plugins
)

# Flask App
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=3000)

async def run_bot():
    await bot.start()
    print("✅ Bot is running...")

    # Background plan expiry tasks
    asyncio.create_task(plan1_expiry(bot))
    asyncio.create_task(plan2_expiry(bot))
    asyncio.create_task(plan3_expiry(bot))
    asyncio.create_task(plan4_expiry(bot))
    asyncio.create_task(plan5_expiry(bot))
    asyncio.create_task(redeem_expiry(bot))

    await idle()
    await bot.stop()
    print("❌ Bot stopped.")

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    # Run Flask in a separate thread
    threading.Thread(target=run_flask).start()

    # Start bot loop
    asyncio.run(run_bot())
