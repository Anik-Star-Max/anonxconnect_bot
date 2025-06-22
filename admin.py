import os
from database import get_user_data, save_user_data, get_all_users, ban_user, unban_user, assign_diamonds

ADMIN_ID = os.getenv("ADMIN_ID")

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

def ban_command(user_id):
    if not is_admin(user_id):
        return "Unauthorized."
    ban_user(user_id)
    return "User has been banned."

def unban_command(user_id):
    if not is_admin(user_id):
        return "Unauthorized."
    unban_user(user_id)
    return "User has been unbanned."

def broadcast_command(message):
    users = get_all_users()
    for user in users:
        # send logic (integrate with bot)
        pass
    return "Broadcast sent."

def assign_diamonds_command(target_user_id, amount):
    if not is_admin(target_user_id):
        assign_diamonds(target_user_id, amount)
        return f"Assigned {amount} diamonds."
    else:
        return "Admin cannot assign diamonds to self."
