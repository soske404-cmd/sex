import json
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from BOT.helper.start import USERS_FILE, load_users, save_users, load_owner_id

PLAN_NAME = "Pro"
PLAN_PRICE = "$3"
PLAN_BADGE = "🔰"
DEFAULT_BADGE = "🧿"
DEFAULT_ANTISPAM = 15
DEFAULT_MLIMIT = 5
PRO_ANTISPAM = 7
PRO_MLIMIT = 7
PRO_CREDIT_BONUS = 500
EXPIRY_SECONDS = 604800 # Set to 30 seconds for testing

OWNER_ID = load_owner_id()

def activate_pro_plan(user_id: str) -> bool:
    users = load_users()
    user = users.get(user_id)
    if not user:
        return False

    # Check if user already has unexpired Pro plan
    plan = user.get("plan", {})
    if plan.get("plan") == PLAN_NAME and plan.get("expires_at"):
        expiry_time = datetime.strptime(plan["expires_at"], "%Y-%m-%d %H:%M:%S")
        if datetime.now() < expiry_time:
            return "already_active"

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expires_at = (datetime.now() + timedelta(seconds=EXPIRY_SECONDS)).strftime("%Y-%m-%d %H:%M:%S")

    # Add credits
    current_credits = user["plan"]["credits"]
    if current_credits != "∞":
        try:
            current_credits = int(current_credits)
            new_credits = current_credits + PRO_CREDIT_BONUS
        except:
            new_credits = PRO_CREDIT_BONUS
    else:
        new_credits = "∞"

    user["plan"].update({
        "plan": PLAN_NAME,
        "activated_at": now,
        "expires_at": expires_at,
        "antispam": PRO_ANTISPAM,
        "mlimit": PRO_MLIMIT,
        "badge": PLAN_BADGE,
        "credits": new_credits,
        "private": "on"
    })
    user["role"] = PLAN_NAME
    save_users(users)
    return True

async def check_and_expire_plans(app: Client):
    while True:
        users = load_users()
        now = datetime.now()
        changed = False

        for user_id, user in users.items():
            plan = user.get("plan", {})

            # Check if the plan exists and has an expiry time
            if plan.get("plan") == PLAN_NAME and plan.get("expires_at"):
                expires_at = plan.get("expires_at")
                
                # If expiry time is valid, process the expiration
                if expires_at:
                    try:
                        expiry_time = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
                        if now >= expiry_time:
                            # Revert to Free plan
                            user["plan"].update({
                                "plan": "Free",
                                "activated_at": user.get("registered_at", plan["activated_at"]),
                                "expires_at": None,
                                "antispam": DEFAULT_ANTISPAM,
                                "mlimit": DEFAULT_MLIMIT,
                                "badge": DEFAULT_BADGE,
                                "private": "off"
                            })
                            user["role"] = "Free"
                            changed = True

                            # Notify the user that the plan expired
                            try:
                                await app.send_message(
                                    int(user_id),
                                    """<pre>Notification ❗️</pre>
<b>~ Your Plan Is Expired</b>
<b>~ Renew your plan</b> (<code>/buy</code>)
<b>~ Contact to Owner at @SosBlastBot</b>
                               """)
                            except Exception as e:
                                print(f"Error sending expiration message: {e}")

                            # Notify the owner
                            try:
                                await app.send_message(
                                    OWNER_ID,
                                    f"ℹ️ Plan for user <code>{user_id}</code> has expired and reverted to Free."
                                )
                            except Exception as e:
                                print(f"Error sending owner notification: {e}")

                    except Exception as e:
                        print(f"Error checking expiry for user {user_id}: {e}")

        if changed:
            save_users(users)

        await asyncio.sleep(5)  # Check every 5 seconds

