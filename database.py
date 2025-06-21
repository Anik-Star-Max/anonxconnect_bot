import json
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.users = self._load_db('users.json')
        self.complaints = self._load_db('complaints.json')
    
    def _load_db(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_users(self):
        with open('users.json', 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def add_user(self, user_id, name):
        if str(user_id) not in self.users:
            self.users[str(user_id)] = {
                'name': name,
                'gender': None,
                'age': None,
                'vip': {'expiry': None, 'diamonds': 0},
                'language': 'en',
                'partner': None,
                'banned': False,
                'reported_count': 0,
                'waiting': False,
                'last_active': datetime.now().isoformat()
            }
            self.save_users()
    
    def update_user(self, user_id, **kwargs):
        user_id = str(user_id)
        if user_id in self.users:
            user = self.users[user_id]
            for key, value in kwargs.items():
                if key == 'diamonds':
                    user['vip']['diamonds'] = value
                elif key == 'vip_expiry':
                    user['vip']['expiry'] = value
                else:
                    user[key] = value
            user['last_active'] = datetime.now().isoformat()
            self.save_users()
            return True
        return False
    
    def get_user(self, user_id):
        return self.users.get(str(user_id))
    
    def is_vip(self, user_id):
        user = self.get_user(user_id)
        if not user or user['banned']:
            return False
        
        expiry = user['vip'].get('expiry')
        if expiry and datetime.fromisoformat(expiry) > datetime.now():
            return True
        return False
    
    def find_match(self, user_id):
        current_user = self.get_user(user_id)
        if not current_user or current_user['banned'] or current_user['partner']:
            return None
        
        for uid, user in self.users.items():
            if (uid != str(user_id) and user['waiting'] and not user['banned'] and not user['partner']:
                return uid
        return None
    
    def cleanup_inactive_users(self):
        now = datetime.now()
        count = 0
        for user_id, user in list(self.users.items()):
            if user['waiting'] or user['partner']:
                try:
                    last_active = datetime.fromisoformat(user['last_active'])
                    if (now - last_active).total_seconds() > INACTIVITY_TIMEOUT:
                        self.update_user(user_id, waiting=False, partner=None)
                        count += 1
                except:
                    pass
        return count
