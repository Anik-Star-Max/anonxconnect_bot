import json
import os
from datetime import datetime, timedelta
from config import (
    USERS_DB, COMPLAINTS_DB, RAILWAY_DB, PHOTO_ROULETTE_DB, 
    CHAT_LOGS_DB, ADMIN_ID, DEFAULT_LANGUAGE, DEFAULT_GENDER, DEFAULT_AGE_RANGE
)

def init_database():
    """Initialize all database files."""
    databases = [
        USERS_DB,
        COMPLAINTS_DB,
        RAILWAY_DB,
        PHOTO_ROULETTE_DB,
        CHAT_LOGS_DB
    ]
                
    for db in databases:
        if not os.path.exists(db):
            with open(db, 'w', encoding='utf-8') as f:
                json.dump({}, f)

def load_json(filename: str) -> dict:
    """Load data from a JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(filename: str, data: dict) -> None:
    """Save data to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving to {filename}: {e}")

def load_users() -> dict:
    """Load user data from the database."""
    return load_json(USERS_DB)

def save_users(users_data: dict) -> None:
    """Save user data to the database."""
    save_json(USERS_DB, users_data)

def get_user(user_id: int) -> dict:
    """Get user data from the database."""
    users = load_users()
    return users.get(str(user_id))

def save_user(user_id: int, user_data: dict) -> None:
    """Save user data to the database."""
    users = load_users()
    users[str(user_id)] = user_data
    save_users(users)

def create_user(user_id: int, username: str, first_name: str) -> dict:
    """Create a new user in the database."""
    user_data = {
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'gender': DEFAULT_GENDER,
        'age': None,
        'language': DEFAULT_LANGUAGE,
        'diamonds': 100,  # Starting diamonds
        'vip_until': None,
        'is_vip': user_id == ADMIN_ID,  # Admin has lifetime VIP
        'banned': False,
        'current_partner': None,
        'waiting_for_partner': False,
        'last_bonus': None,
        'referrals': [],
        'referred_by': None,
        'translation_enabled': False,
        'profile_photo': None,
        'photo_likes': 0,
        'photo_dislikes': 0,
        'preferred_gender': 'any',
        'preferred_age_min': 18,
        'preferred_age_max': 99,
        'created_at': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat()
    }
    save_user(user_id, user_data)
    return user_data

def update_user(user_id: int, **kwargs) -> dict:
    """Update user data."""
    user = get_user(user_id)
    if user:
        user.update(kwargs)
        user['last_active'] = datetime.now().isoformat()
        save_user(user_id, user)
        return user
    return None

def is_user_vip(user_id: int) -> bool:
    """Check if user has VIP status."""
    if user_id == ADMIN_ID:
        return True
    
    user = get_user(user_id)
    if not user or not user.get('vip_until'):
        return False
    
    vip_until = datetime.fromisoformat(user['vip_until'])
    return datetime.now() < vip_until

def add_diamonds(user_id: int, amount: int) -> int:
    """Add diamonds to user."""
    user = get_user(user_id)
    if user:
        user['diamonds'] = user.get('diamonds', 0) + amount
        save_user(user_id, user)
        return user['diamonds']
    return 0

def spend_diamonds(user_id: int, amount: int) -> bool:
    """Spend diamonds from user."""
    user = get_user(user_id)
    if user and user.get('diamonds', 0) >= amount:
        user['diamonds'] -= amount
        save_user(user_id, user)
        return True
    return False

def give_vip(user_id: int, days: int) -> bool:
    """Give VIP status to user."""
    user = get_user(user_id)
    if user:
        if user.get('vip_until'):
            vip_until = datetime.fromisoformat(user['vip_until'])
            new_vip_until = vip_until + timedelta(days=days) if vip_until > datetime.now() else datetime.now() + timedelta(days=days)
        else:
            new_vip_until = datetime.now() + timedelta(days=days)
        
        user['vip_until'] = new_vip_until.isoformat()
        user['is_vip'] = True
        save_user(user_id, user)
        return True
    return False

def find_available_partner(user_id: int) -> str:
    """Find an available partner for the user."""
    users = load_users()
    user = users.get(str(user_id))
    
    if not user:
        return None
    
    available_users = []
    for uid, u in users.items():
        if (uid != str(user_id) and 
            u.get('waiting_for_partner') and 
            not u.get('banned') and 
            not u.get('current_partner')):
            
            # Check if user is VIP and has preferences
            if is_user_vip(user_id):
                # Check gender preference
                if user.get('preferred_gender', 'any') != 'any' and u.get('gender') != user['preferred_gender']:
                    continue
                
                # Check age preference
                if u.get('age'):
                    min_age = user.get('preferred_age_min', 18)
                    max_age = user.get('preferred_age_max', 99)
                    if not (min_age <= u['age'] <= max_age):
                        continue
            
            available_users.append(uid)
    
    return available_users[0] if available_users else None

def connect_users(user1_id: int, user2_id: int) -> None:
    """Connect two users for chat."""
    update_user(user1_id, current_partner=user2_id, waiting_for_partner=False)
    update_user(user2_id, current_partner=user1_id, waiting_for_partner=False)

def disconnect_users(user1_id: int, user2_id: int = None) -> str:
    """Disconnect users from chat."""
    user1 = get_user(user1_id)
    if user1 and user1.get('current_partner'):
        partner_id = user1['current_partner']
        update_user(user1_id, current_partner=None, waiting_for_partner=False)
        update_user(partner_id, current_partner=None, waiting_for_partner=False)
        return partner_id
    return None

def add_complaint(user_id: int, partner_id: int, reason: str) -> str:
    """Add a complaint to the database."""
    complaints = load_json(COMPLAINTS_DB)
    complaint_id = str(len(complaints) + 1)
    
    complaint_data = {
        'id': complaint_id,
        'reporter_id': user_id,
        'reported_id': partner_id,
        'reason': reason,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    complaints[complaint_id] = complaint_data
    save_json(COMPLAINTS_DB, complaints)
    return complaint_id

def log_chat_message(sender_id: int, receiver_id: int, message_type: str, content: str) -> None:
    """Log chat messages for admin monitoring."""
    logs = load_json(CHAT_LOGS_DB)
    log_id = str(len(logs) + 1)
    
    log_data = {
        'id': log_id,
        'sender_id': sender_id,
        'receiver_id': receiver_id,
        'message_type': message_type,
        'content': content[:100] if message_type == 'text' else f'[{message_type}]',
        'timestamp': datetime.now().isoformat()
    }
    
    logs[log_id] = log_data
    save_json(CHAT_LOGS_DB, logs)

def get_user_stats() -> dict:
    """Get bot statistics."""
    users = load_users()
    complaints = load_json(COMPLAINTS_DB)
    
    total_users = len(users)
    active_users = len([u for u in users.values() if u.get('current_partner')])
    vip_users = len([u for u in users.values() if is_user_vip(u['user_id'])])
    banned_users = len([u for u in users.values() if u.get('banned')])
    total_complaints = len(complaints)
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'vip_users': vip_users,
        'banned_users': banned_users,
        'total_complaints': total_complaints
    }

def get_top_referrals(limit: int = 10) -> list:
    """Get top users by referral count."""
    users = load_users()
    referral_counts = []
    
    for user_id, user_data in users.items():
        referral_count = len(user_data.get('referrals', []))
        if referral_count > 0:
            referral_counts.append({
                'user_id': user_id,
                'username': user_data.get('username', 'Unknown'),
                'first_name': user_data.get('first_name', 'Unknown'),
                'referral_count': referral_count
            })
    
    referral_counts.sort(key=lambda x: x['referral_count'], reverse=True)
    return referral_counts[:limit]

def ban_user(user_id: int) -> bool:
    """Ban a user."""
    return update_user(user_id, banned=True, current_partner=None, waiting_for_partner=False)

def unban_user(user_id: int) -> bool:
    """Unban a user."""
    return update_user(user_id, banned=False)
