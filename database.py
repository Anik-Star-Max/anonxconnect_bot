import json
import os
from datetime import datetime, timedelta

def read_db(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, 'r') as f:
        try:
            return json.load(f)
        except:
            return {}

def write_db(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

class Database:
    def __init__(self):
        self.users = read_db('users.json')
        self.complaints = read_db('complaints.json')
    
    def save_users(self):
        write_db(self.users, 'users.json')
    
    def save_complaints(self):
        write_db(self.complaints, 'complaints.json')
    
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
                'last_active': datetime.now().isoformat(),
                'pref_gender': 'any',
                'pref_min_age': 13,
                'pref_max_age': 100
            }
            self.save_users()
    
    def update_user(self, user_id, **kwargs):
        user = self.users.get(str(user_id))
        if user:
            for key, value in kwargs.items():
                if key == 'vip_expiry':
                    user['vip']['expiry'] = value
                elif key == 'diamonds':
                    user['vip']['diamonds'] = value
                else:
                    user[key] = value
            user['last_active'] = datetime.now().isoformat()
            self.save_users()
            return True
        return False
    
    def is_vip(self, user_id):
        user = self.users.get(str(user_id))
        if not user or user['banned']:
            return False
        vip_expiry = user['vip'].get('expiry')
        if vip_expiry and datetime.fromisoformat(vip_expiry) > datetime.now():
            return True
        return False
    
    def add_complaint(self, from_user, against_user, reason):
        complaint_id = f"{datetime.now().timestamp()}"
        self.complaints[complaint_id] = {
            'from_user': from_user,
            'against_user': against_user,
            'reason': reason,
            'resolved': False
        }
        self.save_complaints()
    
    def find_match(self, user_id):
        current_user = self.users.get(str(user_id))
        if not current_user or current_user['banned'] or current_user['partner']:
            return None
        
        preferences = {
            'gender': current_user.get('pref_gender', 'any'),
            'min_age': current_user.get('pref_min_age', 13),
            'max_age': current_user.get('pref_max_age', 100)
        } if self.is_vip(user_id) else {'gender': 'any', 'min_age': 13, 'max_age': 100}
        
        for uid, user in self.users.items():
            if (uid != str(user_id) and 
                user['waiting'] and 
                not user['banned'] and 
                not user['partner']):
                
                # VIP preference matching
                if preferences['gender'] != 'any' and user['gender'] != preferences['gender']:
                    continue
                if user['age'] and (user['age'] < preferences['min_age'] or user['age'] > preferences['max_age']):
                    continue
                
                return uid
        return None
    
    def cleanup_inactive_users(self):
    now = datetime.now()
    inactive_count = 0
    for user_id, user_data in list(self.users.items()):
        if user_data.get('waiting') or user_data.get('partner'):
            try:
                last_active = datetime.fromisoformat(user_data['last_active'])
                if (now - last_active).seconds > self.inactivity_timeout:
                    # Reset user status
                    self.update_user(user_id, waiting=False, partner=None)
                    inactive_count += 1
            except Exception as e:
                logger.error(f"Cleanup error for {user_id}: {str(e)}")
    logger.info(f"Cleaned up {inactive_count} inactive users")
    return inactive_count
