from deep_translator import GoogleTranslator
import logging
from database import get_user, is_vip

logger = logging.getLogger(__name__)

def detect_language(text):
    """Detect the language of the text."""
    try:
        from langdetect import detect
        return detect(text)
    except:
        return 'en'  # Default to English

def translate_message(text, from_lang, to_lang):
    """Translate message from one language to another."""
    if from_lang == to_lang:
        return text
    
    try:
        translator = GoogleTranslator(source=from_lang, target=to_lang)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # Return original text if translation fails

def should_translate(user_id, partner_id, message_text):
    """Check if message should be translated."""
    # Check if user has VIP and translation enabled
    if not is_vip(user_id):
        return False, None, None
    
    user = get_user(user_id)
    partner = get_user(partner_id)
    
    if not user or not partner:
        return False, None, None
    
    # Check if translation is enabled for user
    if not user.get('settings', {}).get('translation', False):
        return False, None, None
    
    user_lang = user.get('language', 'en')
    partner_lang = partner.get('language', 'en')
    
    # If same language, no translation needed
    if user_lang == partner_lang:
        return False, None, None
    
    # Detect message language
    detected_lang = detect_language(message_text)
    
    # If message is already in partner's language, no translation needed
    if detected_lang == partner_lang:
        return False, None, None
    
    return True, detected_lang, partner_lang

def get_translated_message(user_id, partner_id, message_text):
    """Get translated version of message if needed."""
    should_trans, from_lang, to_lang = should_translate(user_id, partner_id, message_text)
    
    if not should_trans:
        return message_text, False
    
    translated = translate_message(message_text, from_lang, to_lang)
    
    # Add translation indicator
    if translated != message_text:
        return f"{translated}\n\n🌐 _Translated from {from_lang.upper()}_", True
    
    return message_text, False
