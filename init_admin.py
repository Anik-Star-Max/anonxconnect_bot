from database import *
from config import ADMIN_ID

def initialize_admin():
    """Initialize admin with lifetime VIP and unlimited diamonds"""
    try:
        # Add admin as user if not exists
        add_user(ADMIN_ID, "mysteryman02")
        
        # Give admin unlimited diamonds (999999)
        user_data = get_user_data(ADMIN_ID)
        user_data['diamonds'] = 999999
        user_data['vip'] = True
        user_data['vip_expires'] = None  # Lifetime VIP
        user_data['is_admin'] = True
        
        # Save admin data
        users = load_users()
        users[str(ADMIN_ID)] = user_data
        save_users(users)
        
        print(f"✅ Admin {ADMIN_ID} initialized with lifetime VIP and unlimited diamonds!")
        
    except Exception as e:
        print(f"❌ Error initializing admin: {e}")

if __name__ == "__main__":
    initialize_admin()
