import json, os, datetime
from telegram import ReplyKeyboardMarkup

USERS_FILE = "users.json"
COMPLAINTS_FILE = "complaints.json"
RULES_FILE = "rules.txt"

def load_json(file):
    if not os.path.exists(file): return {}
    with open(file, "r") as f: return json.load(f)

def save_json(file, data):
    with open(file, "w") as f: json.dump(data, f, indent=2)

def create_or_update_user(user_id, username):
    users = load_json(USERS_FILE)
    user = users.get(str(user_id), {})
    user.update({
        "username": username,
        "vip": user.get("vip", False),
        "language": user.get("language", "en"),
        "diamonds": user.get("diamonds", 0),
        "ban": user.get("ban", False),
        "profile": user.get("profile", {}),
        "referrals": user.get("referrals", 0),
        "partner": user.get("partner", None)
    })
    users[str(user_id)] = user
    save_json(USERS_FILE, users)

def give_daily_bonus(user_id):
    users = load_json(USERS_FILE)
    user = users.get(str(user_id), {})
    today = datetime.date.today().isoformat()
    if user.get("last_bonus") == today:
        return "You already claimed your daily bonus today. Come back tomorrow!"
    user["diamonds"] = user.get("diamonds", 0) + 50
    user["last_bonus"] = today
    users[str(user_id)] = user
    save_json(USERS_FILE, users)
    return "⚕️ You received your daily bonus: 50 💎 diamonds!"

def get_profile(user_id):
    users = load_json(USERS_FILE)
    user = users.get(str(user_id), {})
    text = (
        f"👤 Profile:\n"
        f"Username: {user.get('username')}\n"
        f"VIP: {user.get('vip')}\n"
        f"Diamonds: {user.get('diamonds')}\n"
        f"Language: {user.get('language')}\n"
    )
    return text

def connect_user(user_id):
    # Implement anonymous matching logic here
    return "🔃 Looking for a new chat partner... (Matching logic needed)"

def disconnect_user(user_id):
    # Implement disconnect logic here
    return "🚫 Chat stopped. Type /next to start a new anonymous chat."

def ban_user(user_id):
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users[str(user_id)]["ban"] = True
        save_json(USERS_FILE, users)

def unban_user(user_id):
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users[str(user_id)]["ban"] = False
        save_json(USERS_FILE, users)

def assign_vip_user(user_id, days):
    users = load_json(USERS_FILE)
    user = users.setdefault(str(user_id), {})
    until = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    user["vip"] = True
    user["vip_until"] = until
    users[str(user_id)] = user
    save_json(USERS_FILE, users)

def give_diamonds_user(user_id, amount):
    users = load_json(USERS_FILE)
    user = users.setdefault(str(user_id), {})
    user["diamonds"] = user.get("diamonds", 0) + int(amount)
    users[str(user_id)] = user
    save_json(USERS_FILE, users)

def get_stats():
    users = load_json(USERS_FILE)
    total = len(users)
    vip = sum(1 for u in users.values() if u.get("vip"))
    return f"📊 Stats:\nTotal users: {total}\nVIP users: {vip}"

def get_complaints():
    complaints = load_json(COMPLAINTS_FILE)
    return f"Complaints: {json.dumps(complaints, indent=2)}"

def get_chat_log(user_id):
    # Implement chat log retrieval for admin
    return f"Chat log for user {user_id} (Not implemented)"

async def forward_message(update, mtype):
    # Implement forwarding logic and translation here
    await update.message.reply_text("Message forwarding coming soon.")

def vip_status(user_id):
    users = load_json(USERS_FILE)
    user = users.get(str(user_id), {})
    if user.get("vip") == "lifetime":
        return "👑 You are a lifetime VIP!"
    elif user.get("vip"):
        return f"🎫 Your VIP expires on: {user.get('vip_until')}"
    else:
        return "You are not a VIP. Buy VIP with diamonds!"

def set_translate_status(user_id):
    users = load_json(USERS_FILE)
    user = users.get(str(user_id), {})
    is_vip = user.get("vip", False)
    status = user.get("profile", {}).get("translate", False)
    msg = "Translation is available for VIP users only." if not is_vip else f"Translation is currently {'ON' if status else 'OFF'}."
    keyboard = ReplyKeyboardMarkup([["On"], ["Off"]], resize_keyboard=True)
    return msg, keyboard

def get_rules_text():
    if not os.path.exists(RULES_FILE):
        return "No rules defined."
    with open(RULES_FILE, "r") as f:
        return f.read()
