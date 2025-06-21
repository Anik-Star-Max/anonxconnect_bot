import json
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.users = self.load_data('users.json')
        self.photos = self.load_data('photos.json')
        self.referrals = self.load_data('referrals.json')
        self.top_referrals = []
        
    def load_data(self, filename):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_data(self, data, filename):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def save_users(self):
        self.save_data(self.users, 'users.json')
    
    def save_photos(self):
        self.save_data(self.photos, 'photos.json')
    
    def save_referrals(self):
        self.save_data(self.referrals, 'referrals.json')
    
    def add_user(self, user_id, name, bonus=0):
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {
                'name': name,
                'diamonds': bonus,
                'referrals': 0,
                'chats': 0,
                'rating': 0,
                'language': 'en',
                'partner': None,
                'waiting': False,
                'vip_expiry': None,
                'last_active': datetime.now().isoformat(),
                'public_profile': True,
                'translate_enabled': True,
                'photos': []
            }
            self.save_users()
    
    def get_user(self, user_id):
        return self.users.get(str(user_id))
    
    def update_user(self, user_id, **kwargs):
        user = self.get_user(user_id)
        if user:
            for key, value in kwargs.items():
                user[key] = value
            user['last_active'] = datetime.now().isoformat()
            self.save_users()
            return True
        return False
    
    def is_vip(self, user_id):
        user = self.get_user(user_id)
        if not user:
            return False
        
        # Admin has permanent VIP
        if int(user_id) == config.ADMIN_ID:
            return True
        
        expiry = user.get('vip_expiry')
        if expiry and datetime.fromisoformat(expiry) > datetime.now():
            return True
        return False
    
    def add_photo(self, user_id, photo_id):
        user_id = str(user_id)
        if user_id not in self.photos:
            self.photos[user_id] = []
        
        if len(self.photos[user_id]) < config.MAX_PHOTOS_PER_USER:
            self.photos[user_id].append({
                'id': photo_id,
                'likes': 0,
                'timestamp': datetime.now().isoformat()
            })
            self.save_photos()
            return True
        return False
    
    def like_photo(self, photo_user_id, photo_index):
        photo_user_id = str(photo_user_id)
        if photo_user_id in self.photos and photo_index < len(self.photos[photo_user_id]):
            self.photos[photo_user_id][photo_index]['likes'] += 1
            self.save_photos()
            
            # Reward user
            user = self.get_user(photo_user_id)
            if user:
                user['diamonds'] = user.get('diamonds', 0) + config.PHOTO_LIKE_REWARD
                self.save_users()
            return True
        return False
    
    def add_referral(self, referrer_id, referred_id):
        referral_id = f"{referrer_id}_{referred_id}"
        if referral_id not in self.referrals:
            self.referrals[referral_id] = {
                'referrer': referrer_id,
                'referred': referred_id,
                'timestamp': datetime.now().isoformat()
            }
            self.save_referrals()
            
            # Update user stats
            referrer = self.get_user(referrer_id)
            if referrer:
                referrer['referrals'] = referrer.get('referrals', 0) + 1
                referrer['diamonds'] = referrer.get('diamonds', 0) + config.REFERRAL_BONUS
                self.save_users()
            return True
        return False
    
    def get_top_referrals(self):
        # Calculate top referrals
        referrals = {}
        for user_id, user in self.users.items():
            if user.get('public_profile', True):
                referrals[user_id] = user.get('referrals', 0)
        
        # Sort by referral count
        sorted_referrals = sorted(referrals.items(), key=lambda x: x[1], reverse=True)
        self.top_referrals = sorted_referrals[:config.REFERRAL_TOP_COUNT]
        return self.top_referrals
