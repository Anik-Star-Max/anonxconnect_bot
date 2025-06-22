import database
from config import ADMIN_ID

# Ensure admin always has VIP and is unbanned
admin = database.get_user(ADMIN_ID)

if not admin:
    # Create the admin user without username and first name
    database.create_user(ADMIN_ID, None, None)  # No username or first name

# Give VIP status to the admin for 10 years (3650 days)
database.give_vip(ADMIN_ID, 3650)

# Unban the admin user
database.unban_user(ADMIN_ID)
