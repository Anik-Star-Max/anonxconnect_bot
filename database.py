import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.users = self._load_data('users.json')
        self.complaints = self._load_data('complaints.json')
    
    def _load_data(self, filename):
        """Safely load JSON data"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filename}: {str(e)}")
                return {}
        return {}
    
    def _save_data(self, data, filename):
        """Safely save data to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {str(e)}")
            return False
    
    def save_users(self):
        return self._save_data(self.users, 'users.json')
    
    def save_complaints(self):
        return self._save_data(self.complaints, 'complaints.json')
    
    def add_user(self, user_id, name):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
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
            return self.save_users()
        return False
    
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
            return self.save_users()
        return False
    
    def get_user(self, user_id):
        return self.users.get(str(user_id))
    
    def is_vip(self, user_id):
        user = self.get_user(user_id)
        if user and not user.get('banned', False):
            expiry = user['vip'].get('expiry')
            if expiry:
                try:
                    return datetime.fromisoformat(expiry) > datetime.now()
                except:
                    return False
        return False
    
    def find_match(self, user_id):
        current_user = self.get_user(user_id)
        if not current_user or current_user.get('banned', False) or current_user.get('partner'):
            return None
        
        for partner_id, partner in self.users.items():
            if (partner_id != str(user_id) and 
                partner.get('waiting') and 
                not partner.get('banned', False) and 
                not partner.get('partner')):
                return partner_id
        return None
    
    def cleanup_inactive_users(self):
        now = datetime.now()
        count = 0
        for user_id, user in list(self.users.items()):
            if user.get('waiting') or user.get('partner'):
                try:
                    last_active = datetime.fromisoformat(user['last_active'])
                    if (now - last_active).total_seconds() > 300:  # 5 minutes
                        self.update_user(user_id, waiting=False, partner=None)
                        count += 1
                except:
                    # Reset if timestamp is invalid
                    self.update_user(user_id, last_active=now.isoformat())
        return count
