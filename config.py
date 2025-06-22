import os

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))  # Assuming this variable is always set
BOT_USERNAME = os.getenv('BOT_USERNAME')

# VIP Packages (in diamonds)
VIP_PACKAGES = {
    '1_day': {'price': 500, 'days': 1},
    '2_days': {'price': 1000, 'days': 2},
    '3_days': {'price': 1500, 'days': 3},
    '5_days': {'price': 2000, 'days': 5}
}

# Daily bonus diamonds
DAILY_BONUS = 50

# Photo roulette settings
PHOTO_VOTES_REQUIRED = 5
PHOTO_LIKE_REWARD = 10

# Database file paths
USERS_DB = 'users.json'
COMPLAINTS_DB = 'complaints.json'
RAILWAY_DB = 'railway.json'
PHOTO_ROULETTE_DB = 'photo_roulette.json'
CHAT_LOGS_DB = 'chat_logs.json'

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    '🇺🇸 English': 'en',
    '🇪🇸 Spanish': 'es',
    '🇫🇷 French': 'fr',
    '🇩🇪 German': 'de',
    '🇮🇹 Italian': 'it',
    '🇷🇺 Russian': 'ru',
    '🇨🇳 Chinese': 'zh',
    '🇯🇵 Japanese': 'ja',
    '🇰🇷 Korean': 'ko',
    '🇵🇹 Portuguese': 'pt',
    '🇮🇳 Hindi': 'hi',
    '🇸🇦 Arabic': 'ar'
}

# Default settings
DEFAULT_LANGUAGE = 'en'
DEFAULT_GENDER = 'any'
DEFAULT_AGE_RANGE = [18, 99]
