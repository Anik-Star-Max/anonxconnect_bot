import os

# Core Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")

# VIP System
VIP_PRICES = {
    1: 500,   # 1 day
    7: 2000,  # 1 week
    30: 5000, # 1 month
    365: 15000 # 1 year
}

# Admin Privileges
ADMIN_VIP_EXPIRY = "2100-01-01T00:00:00"
ADMIN_DIAMONDS = 1000000  # Unlimited diamonds

# Referral System
REFERRAL_BONUS = 200  # Diamonds per successful referral
REFERRAL_TOP_COUNT = 10  # Top 10 referrals

# Photo Roulette
MAX_PHOTOS_PER_USER = 5
PHOTO_LIKE_REWARD = 50  # Diamonds per like

# Supported Languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ru': 'Russian',
    'zh': 'Chinese',
    'hi': 'Hindi',
    'ar': 'Arabic',
    'pt': 'Portuguese',
    'ja': 'Japanese'
}

# Inactivity Timeout (minutes)
INACTIVITY_TIMEOUT = 15

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is required!")
