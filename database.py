import json
import os
from datetime import datetime, timedelta
from config import ADMIN_ID

USERS_FILE = "users.json"
QUEUE_FILE = "queue.json"

def _load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def _save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def get_user_data(user_id):
    users = _load_users()
    return users.get(str(user_id), {})

async def add_user(user):
    users = _load_users()
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "id": user.id,
            "name": user.full_name,
            "gender": None,
            "age": None,
            "vip_until": None,
            "diamonds": 0,
            "language": "en",
            "partner": None,
            "banned": False,
            "referrals": [],
            "translate": False,
            "photo": None,
            "allow_account": False,
            "admin": (user.id == ADMIN_ID),
            "joined": datetime.now().isoformat(),
        }
        _save_users(users)

def _get_queue():
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, "w") as f:
            json.dump([], f)
    with open(QUEUE_FILE, "r") as f:
        return json.load(f)

def _save_queue(queue):
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f)

async def start_next_chat(user_id):
    user_id = str(user_id)
    users = _load_users()
    queue = _get_queue()

    # Check banned
    if users.get(user_id, {}).get("banned"):
        return "🚫 You are banned from using the chat."

    # Already chatting?
    if users.get(user_id, {}).get("partner"):
        return "❗ You are already connected to a partner. Use /stop to disconnect first."

    # Remove from queue if already there
    if user_id in queue:
        queue.remove(user_id)

    # Try to find a match
    for other_id in queue:
        if other_id == user_id:
            continue
        if users.get(other_id, {}).get("partner") is not None:
            continue
        users[user_id]["partner"] = int(other_id)
        users[other_id]["partner"] = int(user_id)
        _save_users(users)
        queue.remove(other_id)
        _save_queue(queue)
        return "🎯 Partner found! Say hi 👋"
    # No partner found, add to queue
    queue.append(user_id)
    _save_queue(queue)
    return "⏳ Waiting for a partner... Please wait."

async def stop_current_chat(user_id):
    user_id = str(user_id)
    users = _load_users()
    queue = _get_queue()
    if user_id in queue:
        queue.remove(user_id)
        _save_queue(queue)
        return "🚫 You left the search queue."
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        partner_id = str(partner_id)
        users[user_id]["partner"] = None
        if partner_id in users:
            users[partner_id]["partner"] = None
        _save_users(users)
        return "🚫 You disconnected. Your partner has been notified."
    return "❗ You are not chatting or searching."

def get_partner_id(user_id):
    users = _load_users()
    return users.get(str(user_id), {}).get("partner")

def is_in_chat(user_id):
    users = _load_users()
    return users.get(str(user_id), {}).get("partner") is not None

async def daily_bonus(user_id):
    users = _load_users()
    u = users.get(str(user_id))
    if not u:
        return "Please /start first."
    if "last_bonus" in u and u["last_bonus"] == datetime.now().date().isoformat():
        return "⚕️ You already claimed your daily bonus today."
    u["diamonds"] += 25
    u["last_bonus"] = datetime.now().date().isoformat()
    _save_users(users)
    return "⚕️ You received 25 daily diamonds! 💎"

async def get_profile(user_id):
    u = get_user_data(user_id)
    if not u:
        return "No profile found. Please /start first."
    text = f"""👤 <b>Your Profile</b>
<b>Name:</b> {u.get('name')}
<b>Gender:</b> {u.get('gender','Not set')}
<b>Age:</b> {u.get('age','Not set')}
<b>Language:</b> {u.get('language','en')}
<b>Diamonds:</b> {u.get('diamonds',0) if u.get('admin') else 'Hidden'}
<b>VIP until:</b> {u.get('vip_until','None')}
<b>Banned:</b> {u.get('banned',False)}
"""
    return text

async def is_vip(user_id):
    u = get_user_data(user_id)
    if not u:
        return False
    if u.get("admin"):
        return True
    vip_until = u.get("vip_until")
    if vip_until:
        return datetime.fromisoformat(vip_until) > datetime.now()
    return False

async def get_translate_status(user_id):
    u = get_user_data(user_id)
    return u.get("translate", False)

async def set_translate_status(user_id, status: bool):
    users = _load_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["translate"] = status
        _save_users(users)

async def get_settings_text(user_id):
    u = get_user_data(user_id)
    text = f"""⚙️ <b>Settings</b>
Name: {u.get('name','')}
Gender: {u.get('gender','')}
Age: {u.get('age','')}
Language: {u.get('language','')}
Profile Photo: {"Set" if u.get('photo') else "Not set"}
"""
    return text
