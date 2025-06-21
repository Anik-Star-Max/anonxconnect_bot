import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

VIP_PRICES = {1: 500, 2: 1000, 3: 1500, 5: 2000}
INACTIVITY_TIMEOUT = 300  # 5 minutes in seconds

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required!")
