import json
from database import load_users, save_users, get_user, update_user

class ReferralSystem:
    def __init__(self):
        self.referral_file = "referrals.json"
        self.load_referrals()
    
    def load_referrals(self) -> None:
        """Load referral data from JSON file"""
        try:
            with open(self.referral_file, 'r', encoding='utf-8') as f:
                self.referral_data = json.load(f)
        except FileNotFoundError:
            self.referral_data = {
                "referrals": {},  # user_id: [list of referred user_ids]
                "referred_by": {},  # user_id: referrer_user_id
                "rewards": {}  # user_id: total_rewards_earned
            }
            self.save_referrals()
    
    def save_referrals(self) -> None:
        """Save referral data to JSON file"""
        with open(self.referral_file, 'w', encoding='utf-8') as f:
            json.dump(self.referral_data, f, indent=2, ensure_ascii=False)
    
    def generate_referral_link(self, user_id: int, bot_username: str) -> str:
        """Generate referral link for user"""
        return f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    def process_referral(self, new_user_id: int, referrer_id: int) -> tuple:
        """Process a new referral"""
        new_user_str = str(new_user_id)
        referrer_str = str(referrer_id)
        
        # Check if user was already referred
        if new_user_str in self.referral_data["referred_by"]:
            return False, "User  already referred by someone else"
        
        # Check if trying to refer themselves
        if new_user_str == referrer_str:
            return False, "Cannot refer yourself"
        
        # Add referral relationship
        if referrer_str not in self.referral_data["referrals"]:
            self.referral_data["referrals"][referrer_str] = []
        
        self.referral_data["referrals"][referrer_str].append(new_user_str)
        self.referral_data["referred_by"][new_user_str] = referrer_str
        
        # Reward referrer
        reward_amount = 100  # 100 diamonds per referral
        self.add_referral_reward(referrer_id, reward_amount)
        
        # Reward new user
        new_user_reward = 50  # 50 diamonds for joining via referral
        users = load_users()
        if new_user_str in users:
            users[new_user_str]["diamonds"] = users[new_user_str].get("diamonds", 0) + new_user_reward
            save_users(users)
        
        self.save_referrals()
        return True, f"Referral successful! Referrer earned {reward_amount} diamonds, new user earned {new_user_reward} diamonds"
    
    def add_referral_reward(self, user_id: int, amount: int) -> None:
        """Add reward to user for successful referral"""
        user_str = str(user_id)
        
        # Update referral rewards tracking
        if user_str not in self.referral_data["rewards"]:
            self.referral_data["rewards"][user_str] = 0
        
        self.referral_data["rewards"][user_str] += amount
        
        # Update user's diamond balance
        users = load_users()
        if user_str in users:
            users[user_str]["diamonds"] = users[user_str].get("diamonds", 0) + amount
            save_users(users)
        
        self.save_referrals()
    
    def get_user_referral_stats(self, user_id: int) -> dict:
        """Get user's referral statistics"""
        user_str = str(user_id)
        
        referrals_count = len(self.referral_data["referrals"].get(user_str, []))
        total_rewards = self.referral_data["rewards"].get(user_str, 0)
        referred_by = self.referral_data["referred_by"].get(user_str, None)
        
        return {
            "referrals_count": referrals_count,
            "total_rewards": total_rewards,
            "referred_by": referred_by,
            "referral_list": self.referral_data["referrals"].get(user_str, [])
        }
    
    def get_top_referrers(self, limit: int = 10) -> list:
        """Get top referrers by count"""
        referrer_stats = []
        users = load_users()
        
        for user_id, referral_list in self.referral_data["referrals"].items():
            referral_count = len(referral_list)
            total_rewards = self.referral_data["rewards"].get(user_id, 0)
            
            # Get user info
            user_info = users.get(user_id, {})
            username = user_info.get("username", "Anonymous")
            show_profile = user_info.get("show_in_referral_top", True)
            
            if referral_count > 0:
                referrer_stats.append({
                    "user_id": user_id,
                    "username": username if show_profile else "Anonymous",
                    "referral_count": referral_count,
                    "total_rewards": total_rewards,
                    "show_profile": show_profile
                })
        
        # Sort by referral count descending
        referrer_stats.sort(key=lambda x: x["referral_count"], reverse=True)
        
        return referrer_stats[:limit]
    
    def toggle_referral_visibility(self, user_id: int, show_in_top: bool = True) -> bool:
        """Toggle user's visibility in referral top"""
        users = load_users()
        user_str = str(user_id)
        
        if user_str in users:
            users[user_str]["show_in_referral_top"] = show_in_top
            save_users(users)
            return True
        
        return False
    
    def get_referral_code_from_start(self, start_param: str) -> int:
        """Extract referrer ID from start parameter"""
        if start_param and start_param.startswith("ref_"):
            try:
                referrer_id = int(start_param.replace("ref_", ""))
                return referrer_id
            except ValueError:
                return None
        return None

# Global instance
referral_system = ReferralSystem()
