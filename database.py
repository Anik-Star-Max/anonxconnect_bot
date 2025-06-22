import json
import os

USERS_FILE = "users.json"
COMPLAINTS_FILE = "complaints.json"

def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump([], f)
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def get_user_data(user_id):
    users = load_json(USERS_FILE)
    for user in users:
        if str(user.get("user_id")) == str(user_id):
            return user
    return None

def save_user_data(user):
    users = load_json(USERS_FILE)
    for i, u in enumerate(users):
        if str(u.get("user_id")) == str(user["user_id"]):
            users[i] = user
            break
    else:
        users.append(user)
    save_json(USERS_FILE, users)

def user_exists(user_id):
    return get_user_data(user_id) is not None

def create_user(user_data):
    save_user_data(user_data)

def get_top_referrals():
    # Return sorted top referrals
    pass

def get_vip_status(user_id):
    user = get_user_data(user_id)
    return user.get("vip", False)

def set_vip_status(user_id, status, expiry=None):
    user = get_user_data(user_id)
    if user:
        user["vip"] = status
        user["vip_expiry"] = expiry
        save_user_data(user)

def get_complaints():
    return load_json(COMPLAINTS_FILE)

def set_language(user_id, language):
    user = get_user_data(user_id)
    if user:
        user["language"] = language
        save_user_data(user)

def set_photo(user_id, url):
    user = get_user_data(user_id)
    if user:
        user["photo_url"] = url
        save_user_data(user)

def set_profile(user_id, profile):
    user = get_user_data(user_id)
    if user:
        user["profile"] = profile
        save_user_data(user)

def get_rules():
    if os.path.exists("rules.txt"):
        with open("rules.txt", "r") as f:
            return f.read()
    return "No rules set."

def is_admin(user_id):
    return str(user_id) == os.getenv("ADMIN_ID")

def ban_user(user_id):
    user = get_user_data(user_id)
    if user:
        user["ban"] = True
        save_user_data(user)

def unban_user(user_id):
    user = get_user_data(user_id)
    if user:
        user["ban"] = False
        save_user_data(user)

def broadcast_message(message):
    users = load_json(USERS_FILE)
    # Implement message sending logic in bot
    pass

def assign_diamonds(user_id, amount):
    user = get_user_data(user_id)
    if user:
        user["diamonds"] = user.get("diamonds", 0) + amount
        save_user_data(user)

def get_chat_stats():
    users = load_json(USERS_FILE)
    total = len(users)
    vips = sum(1 for u in users if u.get("vip"))
    return {"total_users": total, "vip_users": vips}

def get_all_users():
    return load_json(USERS_FILE)

def add_referral(user_id, referred_id):
    # Track referrals
    pass
