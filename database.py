import json
import os
from datetime import datetime, timedelta
import logging
import threading

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, inactivity_timeout=300):
        self.inactivity_timeout = inactivity_timeout
        self.lock = threading.Lock()  # Thread-safe operations
        self.users_file = 'users.json'
        self.complaints_file = 'complaints.json'
        self.users = self._load_db(self.users_file)
        self.complaints = self._load_db(self.complaints_file)
        
        # Ensure admin has lifetime VIP
        if os.getenv('ADMIN_ID'):
            self._ensure_admin_vip(int(os.getenv('ADMIN_ID')))

    def _load_db(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading {filename}: {str(e)}")
                return {}
        return {}
    
    def _save_db(self, data, filename):
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving {filename}: {str(e)}")
            return False
    
    def _ensure_admin_vip(self, admin_id):
        admin_id = str(admin_id)
        if admin_id not in self.users:
            self.users[admin_id] = self._create_new_user("Admin")
        self.users[admin_id]['vip']['expiry'] = "2099-12-31T00:00:00"
        self.save_users()
    
    def _create_new_user(self, name):
        return {
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
    
    def save_users(self):
        with self.lock:
            return self._save_db(self.users, self.users_file)
    
    def save_complaints(self):
        with self.lock:
            return self._save_db(self.complaints, self.complaints_file)
    
    def add_user(self, user_id, name):
        user_id = str(user_id)
        with self.lock:
            if user_id not in self.users:
                self.users[user_id] = self._create_new_user(name)
                self.save_users()
                return True
            return False
    
    def update_user(self, user_id, **kwargs):
        user_id = str(user_id)
        with self.lock:
            if user_id not in self.users:
                return False
            
            user = self.users[user_id]
            for key, value in kwargs.items():
                if key in ['vip_expiry', 'diamonds']:
                    if key == 'vip_expiry':
                        user['vip']['expiry'] = value
                    elif key == 'diamonds':
                        user['vip']['diamonds'] = value
                else:
                    user[key] = value
            
            user['last_active'] = datetime.now().isoformat()
            self.save_users()
            return True
    
    def get_user(self, user_id):
        user_id = str(user_id)
        with self.lock:
            return self.users.get(user_id, None)
    
    def is_vip(self, user_id):
        user = self.get_user(user_id)
        if not user or user.get('banned', False):
            return False
        
        vip_expiry = user['vip'].get('expiry')
        if not vip_expiry:
            return False
        
        try:
            expiry_date = datetime.fromisoformat(vip_expiry)
            return expiry_date > datetime.now()
        except:
            return False
    
    def add_complaint(self, from_user, against_user, reason):
        with self.lock:
            complaint_id = f"{datetime.now().timestamp()}"
            self.complaints[complaint_id] = {
                'from_user': from_user,
                'against_user': against_user,
                'reason': reason,
                'resolved': False
            }
            self.save_complaints()
            return True
    
    def find_match(self, user_id):
        current_user = self.get_user(user_id)
        if not current_user or current_user.get('banned') or current_user.get('partner'):
            return None
        
        # Check VIP preferences
        if self.is_vip(user_id):
            preferences = {
                'gender': current_user.get('pref_gender', 'any'),
                'min_age': current_user.get('pref_min_age', 13),
                'max_age': current_user.get('pref_max_age', 100)
            }
        else:
            preferences = {'gender': 'any', 'min_age': 13, 'max_age': 100}
        
        for uid, user in self.users.items():
            if uid == str(user_id):
                continue
                
            if not user.get('waiting') or user.get('banned') or user.get('partner'):
                continue
            
            # Check gender preference
            if preferences['gender'] != 'any' and user.get('gender') != preferences['gender']:
                continue
                
            # Check age preference
            user_age = user.get('age')
            if user_age:
                if user_age < preferences['min_age'] or user_age > preferences['max_age']:
                    continue
            
            return uid
        
        return None
    
    def cleanup_inactive_users(self):
        now = datetime.now()
        count = 0
        
        with self.lock:
            for user_id, user_data in list(self.users.items()):
                try:
                    if user_data.get('waiting') or user_data.get('partner'):
                        last_active = datetime.fromisoformat(user_data['last_active'])
                        if (now - last_active).total_seconds() > self.inactivity_timeout:
                            # Reset user status
                            user_data['waiting'] = False
                            user_data['partner'] = None
                            count += 1
                except Exception as e:
                    logger.error(f"Cleanup error for {user_id}: {str(e)}")
            
            if count > 0:
                self.save_users()
        
        logger.info(f"Cleaned up {count} inactive users")
        return count
