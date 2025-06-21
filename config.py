import os

# Simple configuration - will work 100%
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # Not used in this minimal version

# Just for demonstration
VIP_PRICES = {1: 500, 2: 1000, 3: 1500, 5: 2000}
INACTIVITY_TIMEOUT = 300
