import json
import os
from datetime import datetime, timedelta
from config import *

def init_database():
    """Initialize all database files."""
    # Initialize users.json
    if not os.path.exists(USERS_DB):
        with open(USERS_DB, 'w') as f:
            json.dump({}, f)
    
    # Initialize complaints.json
    if not os.path.exists(COMPLAINTS_DB):
        with open(COMPLAINTS_DB, 'w') as f:
            json.dump({}, f)
    
    # Initialize chat_logs.json
    if not os.path.exists(CHAT_LOGS):
        with open(CHAT_LOGS, 'w') as f:
            json.dump({}, f)
    
    # Initialize railway.json
    railway_config = {
        "build": {
            "builder": "heroku/python"
        },
        "deploy": {
            "startCommand": "python main.py"
        }
    }
    
    if not os.path.exists(RAILWAY_CONFIG):
        with open(RAILWAY_CONFIG, 'w') as f:
            json.dump(railway_config, f, indent=2)

def load_users():
    """Load users from database."""
    try:
        with open(USERS_DB, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_users(users_data):
    """Save users to database."""
    with open(USERS_DB, 'w') as f:
        json.dump(users_data, f, indent=2)

def load_complaints():
    """Load complaints from database."""
    try:
        with open(COMPLAINTS_DB, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_complaints(complaints_data):
    """Save complaints to database."""
    with open(COMPLAINTS_DB, 'w') as f:
        json.dump(complaints_data, f, indent=2)

def load_chat_logs():
    """Load chat logs from database."""
    try:
        with open(CHAT_LOGS, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_chat_logs(chat_data):
    """Save chat logs to database."""
    with open(CHAT_LOGS, 'w') as f:
        json.dump(chat_data, f, indent=2)

def get_user(user_id):
    """Get user data by ID."""
    users = load_users()
    return users.get(str(user_id))

def save_user(user_id, user_data):
    """Save user data."""
    users = load_users()
    users[str(user_id)] = user_data
    save_users(users)

def create_user(user_id, username, first_name):
    """Create new user with default values."""
    user_data = {
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'gender': None,
        'age': None,
        'language': 'en',
        'diamonds': 100,  # Starting diamonds
        'vip_until': None,
        'banned': False,
        'partner': None,
        'waiting': False,
        'referrals': [],
        'referral_count': 0,
        'last_bonus': None,
        'profile_photos': [],
        'photo_likes': 0,
        'settings': {
            'translation': False,
            'show_profile': True,
            'gender_filter': None,
            'age_min': 18,
            'age_max': 99
        },
        'registered': datetime.now().isoformat()
    }
    save_user(user_id, user_data)
    return user_data

def is_vip(user_id):
    """Check if user has active VIP status."""
    if user_id == ADMIN_ID:
        return True
    
    user = get_user(user_id)
    if not user or not user.get('vip_until'):
        return False
    
    vip_until = datetime.fromisoformat(user['vip_until'])
    return datetime.now() < vip_until

def add_vip_days(user_id, days):
    """Add VIP days to user."""
    user = get_user(user_id)
    if not user:
        return False
    
    current_vip = user.get('vip_until')
    if current_vip:
        vip_until = datetime.fromisoformat(current_vip)
        if vip_until > datetime.now():
            new_vip = vip_until + timedelta(days=days)
        else:
            new_vip = datetime.now() + timedelta(days=days)
    else:
        new_vip = datetime.now() + timedelta(days=days)
    
    user['vip_until'] = new_vip.isoformat()
    save_user(user_id, user)
    return True

def add_diamonds(user_id, amount):
    """Add diamonds to user."""
    user = get_user(user_id)
    if not user:
        return False
    
    user['diamonds'] = user.get('diamonds', 0) + amount
    save_user(user_id, user)
    return True

def deduct_diamonds(user_id, amount):
    """Deduct diamonds from user."""
    user = get_user(user_id)
    if not user or user.get('diamonds', 0) < amount:
        return False
    
    user['diamonds'] -= amount
    save_user(user_id, user)
    return True

def find_partner(user_id):
    """Find a suitable partner for the user."""
    users = load_users()
    user = users.get(str(user_id))
    
    if not user:
        return None
    
    # Get user preferences
    gender_filter = user.get('settings', {}).get('gender_filter')
    age_min = user.get('settings', {}).get('age_min', 18)
    age_max = user.get('settings', {}).get('age_max', 99)
    
    # Find waiting users
    for uid, other_user in users.items():
        if (uid != str(user_id) and 
            other_user.get('waiting') and 
            not other_user.get('banned') and
            not other_user.get('partner')):
            
            # Check gender filter (only for VIP users)
            if is_vip(user_id) and gender_filter:
                if other_user.get('gender') != gender_filter:
                    continue
            
            # Check age filter (only for VIP users)
            if is_vip(user_id) and other_user.get('age'):
                if not (age_min <= other_user['age'] <= age_max):
                    continue
            
            return int(uid)
    
    return None

def connect_users(user1_id, user2_id):
    """Connect two users for chat."""
    users = load_users()
    
    if str(user1_id) in users:
        users[str(user1_id)]['partner'] = user2_id
        users[str(user1_id)]['waiting'] = False
    
    if str(user2_id) in users:
        users[str(user2_id)]['partner'] = user1_id
        users[str(user2_id)]['waiting'] = False
    
    save_users(users)

def disconnect_user(user_id):
    """Disconnect user from current chat."""
    users = load_users()
    user = users.get(str(user_id))
    
    if not user:
        return None
    
    partner_id = user.get('partner')
    
    # Clear current user's partner
    users[str(user_id)]['partner'] = None
    users[str(user_id)]['waiting'] = False
    
    # Clear partner's connection
    if partner_id and str(partner_id) in users:
        users[str(partner_id)]['partner'] = None
        users[str(partner_id)]['waiting'] = False
    
    save_users(users)
    return partner_id

def log_message(user_id, partner_id, message_type, content):
    """Log chat messages for admin viewing."""
    chat_logs = load_chat_logs()
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'from_user': user_id,
        'to_user': partner_id,
        'type': message_type,
        'content': content[:500]  # Limit content length
    }
    
    # Create log key for this chat pair
    chat_key = f"{min(user_id, partner_id)}_{max(user_id, partner_id)}"
    
    if chat_key not in chat_logs:
        chat_logs[chat_key] = []
    
    chat_logs[chat_key].append(log_entry)
    
    # Keep only last 100 messages per chat
    chat_logs[chat_key] = chat_logs[chat_key][-100:]
    
    save_chat_logs(chat_logs)

def get_stats():
    """Get bot statistics."""
    users = load_users()
    complaints = load_complaints()
    
    total_users = len(users)
    active_chats = sum(1 for user in users.values() if user.get('partner'))
    waiting_users = sum(1 for user in users.values() if user.get('waiting'))
    vip_users = sum(1 for uid in users.keys() if is_vip(int(uid)))
    banned_users = sum(1 for user in users.values() if user.get('banned'))
    total_complaints = len(complaints)
    
    return {
        'total_users': total_users,
        'active_chats': active_chats // 2,  # Divide by 2 since each chat involves 2 users
        'waiting_users': waiting_users,
        'vip_users': vip_users,
        'banned_users': banned_users,
        'total_complaints': total_complaints
    }
