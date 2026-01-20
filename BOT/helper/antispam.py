import time
from typing import Tuple  # 👈 Add this import

# Temporary runtime storage for last usage (can use Redis for scale)
last_command_usage = {}

def can_run_command(user_id: str, users: dict) -> Tuple[bool, float]:  # 👈 Use Tuple here
    current_time = time.time()
    user = users.get(user_id)
    if not user:
        return False, 0

    antispam = user.get("plan", {}).get("antispam")
    if antispam is None:
        return True, 0  # Owner or no cooldown

    last_used = last_command_usage.get(user_id)
    if last_used is None or (current_time - last_used) >= antispam:
        last_command_usage[user_id] = current_time
        return True, 0

    remaining = antispam - (current_time - last_used)
    return False, round(remaining, 2)
