import json
import os
from datetime import datetime, timedelta
from database import load_users, save_users, load_complaints

class AdminPanel:
    def __init__(self):
        self.admin_id = int(os.getenv('ADMIN_ID', 0))
        self.chat_logs_file = "chat_logs.json"
        self.admin_logs_file = "admin_logs.json"
        self.load_chat_logs()
        self.load_admin_logs()
    
    def load_chat_logs(self):
        """Load chat logs for admin monitoring"""
        try:
            with open(self.chat_logs_file, 'r', encoding='utf-8') as f:
                self.chat_logs = json.load(f)
        except FileNotFoundError:
            self.chat_logs = {}
            self.save_chat_logs()
    
    def save_chat_logs(self):
        """Save chat logs"""
        with open(self.chat_logs_file, 'w', encoding='utf-8') as f:
            json.dump(self.chat_logs, f, indent=2, ensure_ascii=False)
    
    def load_admin_logs(self):
        """Load admin action logs"""
        try:
            with open(self.admin_logs_file, 'r', encoding='utf-8') as f:
                self.admin_logs = json.load(f)
        except FileNotFoundError:
            self.admin_logs = []
            self.save_admin_logs()
    
    def save_admin_logs(self):
        """Save admin action logs"""
        with open(self.admin_logs_file, 'w', encoding='utf-8') as f:
            json.dump(self.admin_logs, f, indent=2, ensure_ascii=False)
    
    def is_admin(self, user_id):
        """Check if user is admin"""
        return user_id == self.admin_id
    
    def log_chat_message(self, user_id, partner_id, message_text, message_type="text"):
        """Log chat message for admin monitoring"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "partner_id": partner_id,
            "message": message_text,
            "type": message_type
        }
        
        # Create chat session key
        chat_key = f"{min(user_id, partner_id)}_{max(user_id, partner_id)}"
        
        if chat_key not in self.chat_logs:
            self.chat_logs[chat_key] = []
        
        self.chat_logs[chat_key].append(log_entry)
        
        # Keep only last 100 messages per chat
        if len(self.chat_logs[chat_key]) > 100:
            self.chat_logs[chat_key] = self.chat_logs[chat_key][-100:]
        
        self.save_chat_logs()
    
    def log_admin_action(self, action, target_user_id=None, details=""):
        """Log admin actions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "admin_id": self.admin_id,
            "action": action,
            "target_user_id": target_user_id,
            "details": details
        }
        
        self.admin_logs.append(log_entry)
        
        # Keep only last 1000 admin actions
        if len(self.admin_logs) > 1000:
            self.admin_logs = self.admin_logs[-1000:]
        
        self.save_admin_logs()
    
    def ban_user(self, user_id, reason="No reason provided"):
        """Ban a user"""
        users = load_users()
        user_str = str(user_id)
        
        if user_str in users:
            users[user_str]["banned"] = True
            users[user_str]["ban_reason"] = reason
            users[user_str]["ban_date"] = datetime.now().isoformat()
            save_users(users)
            
            self.log_admin_action("BAN_USER", user_id, f"Reason: {reason}")
            return True, f"User {user_id} has been banned. Reason: {reason}"
        
        return False, "User not found"
    
    def unban_user(self, user_id):
        """Unban a user"""
        users = load_users()
        user_str = str(user_id)
        
        if user_str in users:
            users[user_str]["banned"] = False
            users[user_str]["ban_reason"] = ""
            users[user_str]["unban_date"] = datetime.now().isoformat()
            save_users(users)
            
            self.log_admin_action("UNBAN_USER", user_id)
            return True, f"User {user_id} has been unbanned"
        
        return False, "User not found"
    
    def give_diamonds(self, user_id, amount):
        """Give diamonds to a user"""
        users = load_users()
        user_str = str(user_id)
        
        if user_str in users:
            current_diamonds = users[user_str].get("diamonds", 0)
            users[user_str]["diamonds"] = current_diamonds + amount
            save_users(users)
            
            self.log_admin_action("GIVE_DIAMONDS", user_id, f"Amount: {amount}")
            return True, f"Gave {amount} diamonds to user {user_id}. New balance: {current_diamonds + amount}"
        
        return False, "User not found"
    
    def give_vip(self, user_id, days):
        """Give VIP status to a user"""
        users = load_users()
        user_str = str(user_id)
        
        if user_str in users:
            current_vip = users[user_str].get("vip_expires", datetime.now().isoformat())
            try:
                current_vip_date = datetime.fromisoformat(current_vip)
            except:
                current_vip_date = datetime.now()
            
            # If current VIP is expired, start from now
            if current_vip_date < datetime.now():
                current_vip_date = datetime.now()
            
            new_vip_date = current_vip_date + timedelta(days=days)
            users[user_str]["vip_expires"] = new_vip_date.isoformat()
            users[user_str]["is_vip"] = True
            save_users(users)
            
            self.log_admin_action("GIVE_VIP", user_id, f"Days: {days}")
            return True, f"Gave {days} days VIP to user {user_id}. Expires: {new_vip_date.strftime('%Y-%m-%d %H:%M')}"
        
        return False, "User not found"
    
    def get_user_info(self, user_id):
        """Get detailed user information"""
        users = load_users()
        user_str = str(user_id)
        
        if user_str in users:
            user_data = users[user_str].copy()
            
            # Add admin-specific info
            user_data["user_id"] = user_id
            user_data["registration_date"] = user_data.get("registration_date", "Unknown")
            user_data["last_active"] = user_data.get("last_active", "Unknown")
            user_data["total_chats"] = user_data.get("total_chats", 0)
            
            return user_data
        
        return None
    
    def get_chat_logs(self, user_id=None, limit=50):
        """Get chat logs for monitoring"""
        if user_id:
            # Get logs for specific user
            user_logs = []
            for chat_key, messages in self.chat_logs.items():
                if str(user_id) in chat_key:
                    user_logs.extend(messages)
            
            # Sort by timestamp and limit
            user_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            return user_logs[:limit]
        else:
            # Get all recent logs
            all_logs = []
            for messages in self.chat_logs.values():
                all_logs.extend(messages)
            
            all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
            return all_logs[:limit]
    
    def get_stats(self):
        """Get bot statistics"""
        users = load_users()
        complaints = load_complaints()
        
        total_users = len(users)
        active_users = sum(1 for user in users.values() if not user.get("banned", False))
        banned_users = sum(1 for user in users.values() if user.get("banned", False))
        vip_users = sum(1 for user in users.values() if user.get("is_vip", False))
        
        # Calculate today's registrations
        today = datetime.now().date()
        today_registrations = 0
        for user in users.values():
            reg_date = user.get("registration_date", "")
            try:
                if datetime.fromisoformat(reg_date).date() == today:
                    today_registrations += 1
            except:
                pass
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "banned_users": banned_users,
            "vip_users": vip_users,
            "today_registrations": today_registrations,
            "total_complaints": len(complaints),
            "total_chat_sessions": len(self.chat_logs)
        }
    
    def broadcast_message(self, message_text, target_group="all"):
        """Prepare broadcast message data"""
        users = load_users()
        target_users = []
        
        for user_id, user_data in users.items():
            if user_data.get("banned", False):
                continue
            
            if target_group == "all":
                target_users.append(int(user_id))
            elif target_group == "vip" and user_data.get("is_vip", False):
                target_users.append(int(user_id))
            elif target_group == "regular" and not user_data.get("is_vip", False):
                target_users.append(int(user_id))
        
        self.log_admin_action("BROADCAST", None, f"Target: {target_group}, Users: {len(target_users)}")
        
        return target_users, message_text

# Global instance
admin_panel = AdminPanel()
