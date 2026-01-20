import json
import os


def deduct_credit(user_id):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)

        user = users.get(str(user_id))
        if not user:
            return False, "User not found."

        credits = user["plan"].get("credits", 0)

        # If user has credits set to '∞' (infinite), do not deduct
        if credits == "∞":
            return True, "Owner has infinite credits, no deduction necessary."

        # Deduct 1 credit if user has enough credits
        if int(credits) > 0:
            new_credits = int(credits) - 1
            user["plan"]["credits"] = str(new_credits)
            users[str(user_id)] = user
            with open("DATA/users.json", "w") as f:
                json.dump(users, f)
            return True, "Credit deducted successfully."

        return False, "Insufficient credits."

    except Exception as e:
        print(f"[deduct_credit error] {e}")
        return False, "An error occurred while deducting credits."

def has_credits(user_id):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)

        user = users.get(str(user_id))
        if not user:
            return False

        credits = user["plan"].get("credits", 0)
        # Owner gets infinity credit so we return True for them
        if credits == "∞":
            return True
        return int(credits) > 0  # If credit is more than 0, it's okay to proceed
    except Exception as e:
        print(f"[has_credits error] {e}")
        return False

def deduct_credit_bulk(user_id, amount):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)

        user = users.get(str(user_id))
        if not user:
            return False, "User not found."

        credits = user["plan"].get("credits", 0)

        # Handle infinite credits
        if isinstance(credits, str) and credits.strip() == "∞":
            return True, "Infinite credits, no deduction needed."

        # Ensure credits is an integer
        try:
            credits = int(credits)
        except ValueError:
            return False, "Invalid credit format."

        if credits >= amount:
            user["plan"]["credits"] = str(credits - amount)
            users[str(user_id)] = user
            with open("DATA/users.json", "w") as f:
                json.dump(users, f, indent=4)
            return True, f"Deducted {amount} credits successfully."
        else:
            return False, "Insufficient credits."

    except Exception as e:
        print(f"[deduct_credit_bulk error] {e}")
        return False, "Error during bulk deduction."

