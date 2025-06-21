import json
import time
import os
from config import ADMIN_ID

USERS_FILE = "users.json"
COMPLAINTS_FILE = "complaints.json"
REFERRALS_FILE = "referrals.json"

# --- User data helpers ---

def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_user(user_id):
    users = load_users()
    return users.get(str(user_id), None)

def create_user(user_id, name):
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "name": name,
            "gender": "unset",
            "age": 0,
            "diamonds": 0,
            "vip": {"status": False, "expires": 0},
            "language": "en",
            "translation": False,
            "current_partner": None,
            "ban": False,
            "referrals": 0,
            "photo_likes": 0
        }
        save_users(users)

def update_user(user_id, new_data):
    users = load_users()
    users[str(user_id)].update(new_data)
    save_users(users)

def get_partner(user_id):
    user = get_user(user_id)
    if user:
        return user.get("current_partner", None)
    return None

def leave_chat(user_id):
    users = load_users()
    user = users.get(str(user_id))
    if not user or not user["current_partner"]:
        return False
    # Notify partner
    partner_id = user["current_partner"]
    if partner_id and str(partner_id) in users:
        users[str(partner_id)]["current_partner"] = None
    user["current_partner"] = None
    save_users(users)
    return True

QUEUE = []

def match_user(user_id):
    users = load_users()
    user = users.get(str(user_id))
    if not user or user.get("ban"):
        return False
    if user_id in QUEUE:
        return False
    # Find another available user
    for uid, data in users.items():
        if int(uid) != user_id and data.get("current_partner") is None and not data.get("ban") and int(uid) not in QUEUE:
            # Connect both
            users[str(user_id)]["current_partner"] = int(uid)
            users[uid]["current_partner"] = user_id
            save_users(users)
            return True
    # If not found, add to queue
    QUEUE.append(user_id)
    return False

def claim_bonus(user_id):
    users = load_users()
    user = users.get(str(user_id))
    now = int(time.time())
    last_bonus = user.get("last_bonus", 0)
    if now - last_bonus > 24*60*60:
        reward = 50 if not user["vip"]["status"] else 150
        user["diamonds"] += reward
        user["last_bonus"] = now
        save_users(users)
        return f"⚕️ Daily bonus received! +{reward}💎"
    return "You already claimed your bonus today."

def photo_roulette(user_id):
    # For demo. Save photo in your app and allow like/see next
    return "Not implemented yet."

def get_referral_code(user_id):
    return str(user_id)  # Just use user ID for simplicity

def get_top_referrals():
    users = load_users()
    ranking = sorted([(u['name'], u.get('referrals',0)) for u in users.values()], key=lambda x: x[1], reverse=True)
    return ranking[:5]

def give_vip(user_id, days):
    users = load_users()
    user = users.get(str(user_id))
    if not user:
        return "User not found."
    now = int(time.time())
    expire = now + days*24*60*60
    user["vip"] = {"status": True, "expires": expire}
    save_users(users)
    return f"VIP given for {days} days to {user['name']}"

def ban_user(user_id):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["ban"] = True
        save_users(users)
        return True
    return False

def unban_user(user_id):
    users = load_users()
    if str(user_id) in users:
        users[str(user_id)]["ban"] = False
        save_users(users)
        return True
    return False

def broadcast(message):
    users = load_users()
    # Actually sending happens from handlers
    pass

def get_stats():
    users = load_users()
    return f"Total users: {len(users)}"

def is_translation_on(user_id):
    user = get_user(user_id)
    if user:
        return user.get("translation", False)
    return False

# This is just a stub for reporting - expand as needed
def add_complaint(user_id, text):
    if not os.path.exists(COMPLAINTS_FILE):
        with open(COMPLAINTS_FILE, "w") as f:
            json.dump({}, f)
    with open(COMPLAINTS_FILE, "r+") as f:
        complaints = json.load(f)
        nid = str(len(complaints)+1)
        complaints[nid] = {"user_id": user_id, "text": text, "time": int(time.time())}
        f.seek(0)
        json.dump(complaints, f, indent=2)
        f.truncate()
