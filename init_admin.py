import os
import database

def create_admin():
    admin_id = os.getenv("ADMIN_ID")
    admin_username = os.getenv("BOT_USERNAME", "admin")

    admin_data = {
        "user_id": admin_id,
        "username": admin_username,
        "gender": "admin",
        "age": None,
        "vip": "lifetime",
        "vip_expiry": None,
        "diamonds": 9999999,
        "language": "en",
        "current_partner": None,
        "ban": False,
        "is_admin": True,
        "allow_referral_top": True,
        "photo_url": None,
        "profile": {},
        "settings": {}
    }

    if database.user_exists(admin_id):
        print(f"Admin user with ID {admin_id} already exists.")
    else:
        database.create_user(admin_data)
        print(f"Admin user '{admin_username}' with ID {admin_id} created successfully and granted lifetime VIP.")

if __name__ == "__main__":
    create_admin()
