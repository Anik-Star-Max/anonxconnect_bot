import os

# Get environment variables with safety checks
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable is required!")

# Optional ADMIN_ID
ADMIN_ID = os.getenv("ADMIN_ID", "")

# Other configuration
VIP_PRICES = {1: 500, 2: 1000, 3: 1500, 5: 2000}
INACTIVITY_TIMEOUT = 300
