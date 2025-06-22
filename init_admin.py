import database
from config import ADMIN_ID

# Ensure admin always has VIP and is unbanned
admin = database.get_user(ADMIN_ID)
if not admin:
    database.create_user(ADMIN_ID, None)  
database.give_vip(ADMIN_ID, 3650)
database.unban_user(ADMIN_ID)
