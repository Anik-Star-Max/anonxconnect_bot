import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Database file paths
USERS_DB = 'users.json'
COMPLAINTS_DB = 'complaints.json'
RAILWAY_DB = 'railway.json'
PHOTOS_DB = 'photo_roulette.json'
REFERRALS_DB = 'referrals.json'

def init_database():
    """Initialize all database files if they don't exist."""
    databases = {
        USERS_DB: {},
        COMPLAINTS_DB: [],
        RAILWAY_DB: {},
        PHOTOS_DB: {},
        REFERRALS_DB: {}
    }
    
    for db_file, default_data in databases.items():
        if not os.path.exists(db_file):
            save_data(db_file, default_data)

def load_data(filename: str):
    """Load data from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if filename != COMPLAINTS_DB else []

def save_data(filename: str, data):
    """Save data to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(user_id: int) -> Dict:
    """Get user data from database."""
    users = load_data(USERS_DB)
    return users.get(str(user_id), {})

def save_user(user_id: int, user_data: Dict):
    """Save user data to database."""
    users = load_data(USERS_DB)
    users[str(user_id)] = user_data
    save_data(USERS_DB, users)

def create_user(user_id: int, first_name: str, username: str = None) -> Dict:
    """Create a new user in the database."""
    user_data = {
        'user_id': user_id,
        'first_name': first_name,
        'username': username,
        'gender': None,
        'age': None,
        'language': 'en',
        'diamonds': 100,  # Starting diamonds
        'vip_until': None,
        'is_banned': False,
        'partner_id': None,
        'waiting_for_partner': False,
        'joined_date': datetime.now().isoformat(),
        'last_bonus': None,
        'total_chats': 0,
        'referral_code': f"REF{user_id}",
        'referred_by': None,
        'referral_count': 0,
        'translation_enabled': False,
        'profile_visible': True,
        'photo_ids': [],
        'photo_likes': 0,
        'settings': {
            'show_profile_in_referral': True,
            'allow_photo_roulette': True,
            'vip_feedback': True  # Allow like/dislike for VIP
        }
    }
    save_user(user_id, user_data)
    return user_data

def is_vip(user_id: int) -> bool:
    """Check if user has active VIP status."""
    from config import ADMIN_ID
    
    if user_id == ADMIN_ID:
        return True  # Admin has lifetime VIP
    
    user = get_user(user_id)
    if not user.get('vip_until'):
        return False
    
    vip_until = datetime.fromisoformat(user['vip_until'])
    return datetime.now() < vip_until

def add_diamonds(user_id: int, amount: int):
    """Add diamonds to user account."""
    user = get_user(user_id)
    if user:
        user['diamonds'] = user.get('diamonds', 0) + amount
        save_user(user_id, user)

def spend_diamonds(user_id: int, amount: int) -> bool:
    """Spend diamonds from user account. Returns True if successful."""
    user = get_user(user_id)
    if user and user.get('diamonds', 0) >= amount:
        user['diamonds'] -= amount
        save_user(user_id, user)
        return True
    return False

def set_vip(user_id: int, days: int):
    """Set VIP status for user."""
    user = get_user(user_id)
    if user:
        vip_until = datetime.now() + timedelta(days=days)
        user['vip_until'] = vip_until.isoformat()
        save_user(user_id, user)

def add_complaint(user_id: int, reported_user_id: int, message: str):
    """Add a complaint to the database."""
    complaints = load_data(COMPLAINTS_DB)
    complaint = {
        'id': len(complaints) + 1,
        'reporter_id': user_id,
        'reported_user_id': reported_user_id,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    complaints.append(complaint)
    save_data(COMPLAINTS_DB, complaints)
    return complaint

def get_all_users() -> Dict:
    """Get all users from database."""
    return load_data(USERS_DB)

def ban_user(user_id: int):
    """Ban a user."""
    user = get_user(user_id)
    if user:
        user['is_banned'] = True
        save_user(user_id, user)

def unban_user(user_id: int):
    """Unban a user."""
    user = get_user(user_id)
    if user:
        user['is_banned'] = False
        save_user(user_id, user)

def is_banned(user_id: int) -> bool:
    """Check if user is banned."""
    user = get_user(user_id)
    return user.get('is_banned', False)

def find_partner(user_id: int, gender_filter: str = None, age_min: int = None, age_max: int = None) -> Optional[int]:
    """Find a suitable partner for chat."""
    users = get_all_users()
    current_user = get_user(user_id)
    
    available_users = []
    for uid, user_data in users.items():
        uid = int(uid)
        if (uid != user_id and 
            user_data.get('waiting_for_partner') and 
            not user_data.get('is_banned') and
            not user_data.get('partner_id')):
            
            # Apply filters for VIP users
            if gender_filter and user_data.get('gender') != gender_filter:
                continue
            if age_min and (not user_data.get('age') or user_data['age'] < age_min):
                continue
            if age_max and (not user_data.get('age') or user_data['age'] > age_max):
                continue
                
            available_users.append(uid)
    
    return available_users[0] if available_users else None

def connect_users(user1_id: int, user2_id: int):
    """Connect two users for chat."""
    user1 = get_user(user1_id)
    user2 = get_user(user2_id)
    
    if user1 and user2:
        user1['partner_id'] = user2_id
        user1['waiting_for_partner'] = False
        user1['total_chats'] = user1.get('total_chats', 0) + 1
        
        user2['partner_id'] = user1_id
        user2['waiting_for_partner'] = False
        user2['total_chats'] = user2.get('total_chats', 0) + 1
        
        save_user(user1_id, user1)
        save_user(user2_id, user2)

def disconnect_users(user_id: int):
    """Disconnect user from current chat."""
    user = get_user(user_id)
    if user and user.get('partner_id'):
        partner_id = user['partner_id']
        partner = get_user(partner_id)
        
        # Disconnect both users
        user['partner_id'] = None
        user['waiting_for_partner'] = False
        save_user(user_id, user)
        
        if partner:
            partner['partner_id'] = None
            partner['waiting_for_partner'] = False
            save_user(partner_id, partner)
        
        return partner_id
    return None

def can_claim_bonus(user_id: int) -> bool:
    """Check if user can claim daily bonus."""
    user = get_user(user_id)
    if not user.get('last_bonus'):
        return True
    
    last_bonus = datetime.fromisoformat(user['last_bonus'])
    return datetime.now() - last_bonus >= timedelta(days=1)

def claim_bonus(user_id: int, amount: int):
    """Claim daily bonus."""
    user = get_user(user_id)
    if user:
        user['last_bonus'] = datetime.now().isoformat()
        user['diamonds'] = user.get('diamonds', 0) + amount
        save_user(user_id, user)

def add_photo(user_id: int, photo_id: str):
    """Add photo to user's photo roulette."""
    photos = load_data(PHOTOS_DB)
    if str(user_id) not in photos:
        photos[str(user_id)] = []
    
    photos[str(user_id)].append({
        'photo_id': photo_id,
        'likes': 0,
        'uploaded_at': datetime.now().isoformat()
    })
    save_data(PHOTOS_DB, photos)

def like_photo(liker_id: int, owner_id: int, photo_id: str):
    """Like a photo in photo roulette."""
    photos = load_data(PHOTOS_DB)
    if str(owner_id) in photos:
        for photo in photos[str(owner_id)]:
            if photo['photo_id'] == photo_id:
                photo['likes'] += 1
                save_data(PHOTOS_DB, photos)
                
                # Reward photo owner
                add_diamonds(owner_id, 10)
                return True
    return False

def get_referral_top() -> List[Dict]:
    """Get top referral users."""
    users = get_all_users()
    referral_list = []
    
    for user_id, user_data in users.items():
        if user_data.get('referral_count', 0) > 0:
            referral_list.append({
                'user_id': int(user_id),
                'name': user_data.get('first_name', 'Unknown'),
                'username': user_data.get('username'),
                'referral_count': user_data.get('referral_count', 0),
                'show_profile': user_data.get('settings', {}).get('show_profile_in_referral', True)
            })
    
    return sorted(referral_list, key=lambda x: x['referral_count'], reverse=True)[:10]

def process_referral(referrer_code: str, new_user_id: int) -> bool:
    """Process referral when new user joins."""
    users = get_all_users()
    
    for user_id, user_data in users.items():
        if user_data.get('referral_code') == referrer_code:
            referrer_id = int(user_id)
            
            # Add referral bonus to referrer
            add_diamonds(referrer_id, 100)
            
            # Update referrer's count
            user_data['referral_count'] = user_data.get('referral_count', 0) + 1
            save_user(referrer_id, user_data)
            
            # Update new user's referred_by
            new_user = get_user(new_user_id)
            if new_user:
                new_user['referred_by'] = referrer_id
                save_user(new_user_id, new_user)
            
            return True
    return False
