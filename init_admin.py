import json
import os
from datetime import datetime
import config

def initialize_admin():
    # Load or create users.json
    users = {}
    if os.path.exists('users.json'):
        try:
            with open('users.json', 'r') as f:
                users = json.load(f)
        except:
            users = {}
    
    # Create admin profile
    admin_id = str(config.ADMIN_ID)
    users[admin_id] = {
        'name': 'Admin User',
        'is_admin': True,
        'vip_expiry': config.ADMIN_VIP_EXPIRY,
        'diamonds': config.ADMIN_DIAMONDS,
        'referrals': 0,
        'chats': 0,
        'rating': 5,
        'language': 'en',
        'partner': None,
        'waiting': False,
        'public_profile': False,
        'translate_enabled': True,
        'photos': [],
        'last_active': datetime.now().isoformat()
    }
    
    # Save to file
    with open('users.json', 'w') as f:
        json.dump(users, f, indent=2)
    
    print(f"✅ Admin {config.ADMIN_ID} initialized with lifetime VIP access")

if __name__ == '__main__':
    initialize_admin()
