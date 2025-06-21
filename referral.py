import config

def generate_referral_link(user_id):
    return f"https://t.me/{config.BOT_USERNAME}?start=ref_{user_id}"

def is_valid_referral(referral_code):
    return referral_code.startswith('ref_') and referral_code.split('_')[1].isdigit()
