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
                'last_active': datetime.now().isoformat()
            }
            self.save_users()
    
    def update_user(self, user_id, **kwargs):
        user = self.users.get(str(user_id))
        if user:
            for key, value in kwargs.items():
                if key == 'vip_expiry' and value:
                    user['vip']['expiry'] = value
                elif key == 'diamonds':
                    user['vip']['diamonds'] = value
                else:
                    user[key] = value
            user['last_active'] = datetime.now().isoformat()
            self.save_users()
    
    def is_vip(self, user_id):
        user = self.users.get(str(user_id))
        if not user or user['banned']:
            return False
        
        vip_expiry = user['vip'].get('expiry')
        if vip_expiry and datetime.fromisoformat(vip_expiry) > datetime.now():
            return True
        return False
    
    def add_complaint(self, from_user, against_user, reason):
        self.complaints[str(datetime.now())] = {
            'from_user': from_user,
            'against_user': against_user,
            'reason': reason
        }
        self.save_complaints()
    
    def find_match(self, user_id):
        current_user = self.users.get(str(user_id))
        if not current_user or current_user['banned'] or current_user['partner']:
            return None
        
        preferences = {}
        if self.is_vip(user_id):
            preferences = {
                'gender': current_user.get('pref_gender', 'any'),
                'min_age': current_user.get('pref_min_age', 0),
                'max_age': current_user.get('pref_max_age', 100)
            }
        
        for uid, user in self.users.items():
            if (uid != str(user_id) and 
                user['waiting'] and 
                not user['banned'] and 
                not user['partner']):
                
                # Check VIP preferences
                if preferences['gender'] != 'any' and user['gender'] != preferences['gender']:
                    continue
                if user['age'] and (user['age'] < preferences['min_age'] or user['age'] > preferences['max_age']):
                    continue
                
                return uid
        return None
