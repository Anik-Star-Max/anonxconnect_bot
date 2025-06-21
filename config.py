import os

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))  # Replace with actual admin ID
BOT_USERNAME = os.getenv('BOT_USERNAME', 'YourBotUsername')

# VIP packages (days: diamonds cost)
VIP_PACKAGES = {
    1: 500,    # 1 day = 500 diamonds
    2: 1000,   # 2 days = 1000 diamonds
    3: 1500,   # 3 days = 1500 diamonds
    5: 2000    # 5 days = 2000 diamonds
}

# Daily bonus diamonds
DAILY_BONUS = 50

# Supported languages for translation
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'pt': 'Portuguese',
    'tr': 'Turkish',
    'nl': 'Dutch',
    'sv': 'Swedish'
}

# Photo roulette settings
MAX_PHOTOS_PER_USER = 5
PHOTO_LIKE_REWARD = 10  # Diamonds reward for getting likes

# Referral system
REFERRAL_BONUS = 100  # Diamonds for successful referral
