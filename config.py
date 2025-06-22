import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'YourBotUsername')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# VIP Packages (days: diamonds)
VIP_PACKAGES = {
    1: 500,
    2: 1000,
    3: 1500,
    5: 2000
}

# Daily bonus diamonds
DAILY_BONUS = 50

# Photo roulette settings
MAX_PHOTOS_PER_USER = 5

# Translation languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'hi': 'Hindi',
    'ar': 'Arabic',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'tr': 'Turkish',
    'pl': 'Polish',
    'nl': 'Dutch'
}

# File paths
USERS_DB = 'users.json'
COMPLAINTS_DB = 'complaints.json'
RAILWAY_CONFIG = 'railway.json'
RULES_FILE = 'rules.txt'
CHAT_LOGS = 'chat_logs.json'

# Messages
WELCOME_MESSAGE = """
🌟 Welcome to Anonymous Chat Bot! 🌟

🔒 Chat anonymously with strangers worldwide
🌍 Meet new people without revealing your identity
💎 Earn diamonds and get VIP features
🎁 Daily bonuses and referral rewards

Choose your gender and age to get started!

/menu - Access all features
/rules - Read our community guidelines
"""

VIP_FEATURES = """
💎 VIP Features:

✅ Gender Selection - Choose who to chat with
✅ Age Range Filter - Set preferred age range
✅ Profile Preview - See basic info before chat
✅ Priority Matching - Get matched faster
✅ Translation Service - Auto-translate messages
✅ Photo Roulette - Upload and rate photos
✅ Extended Settings - More customization options

💰 VIP Packages:
1 Day - 500 💎
2 Days - 1000 💎
3 Days - 1500 💎
5 Days - 2000 💎
"""
