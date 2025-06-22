from deep_translator import GoogleTranslator
import logging
from database import get_user, is_user_vip

logger = logging.getLogger(__name__)

def detect_language(text):
    """Detect the language of the given text."""
    try:
        # Use Google Translator to detect language
        translator = GoogleTranslator(source='auto', target='en')
        detected = translator.translate(text)
        # Note: This is a simplified detection, in real implementation
        # you might want to use a proper language detection library
        return 'auto'
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return 'en'

def translate_message(text, target_language='en', source_language='auto'):
    """Translate message to target language."""
    try:
        if source_language == target_language:
            return text
        
        translator = GoogleTranslator(source=source_language, target=target_language)
        translated = translator.translate(text)
        return translated
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text  # Return original text if translation fails

def should_translate(sender_id, receiver_id):
    """Check if message should be translated."""
    sender = get_user(sender_id)
    receiver = get_user(receiver_id)
    
    if not sender or not receiver:
        return False
    
    # Check if either user is VIP and has translation enabled
    sender_can_translate = (is_user_vip(sender_id) and 
                           sender.get('translation_enabled', False))
    receiver_can_translate = (is_user_vip(receiver_id) and 
                             receiver.get('translation_enabled', False))
    
    if not (sender_can_translate or receiver_can_translate):
        return False
    
    # Check if users have different languages
    sender_lang = sender.get('language', 'en')
    receiver_lang = receiver.get('language', 'en')
    
    return sender_lang != receiver_lang

def get_translation_info(sender_id, receiver_id, text):
    """Get translation information for a message."""
    sender = get_user(sender_id)
    receiver = get_user(receiver_id)
    
    if not should_translate(sender_id, receiver_id):
        return text, False
    
    sender_lang = sender.get('language', 'en')
    receiver_lang = receiver.get('language', 'en')
    
    # Translate to receiver's language
    translated_text = translate_message(text, receiver_lang, sender_lang)
    
    return translated_text, True

def format_translated_message(original_text, translated_text, sender_lang, receiver_lang):
    """Format translated message with original text."""
    if original_text == translated_text:
        return original_text
    
    return f"{translated_text}\n\n🔄 <i>Translated from {sender_lang} to {receiver_lang}</i>"

def get_available_languages():
    """Get list of available languages for translation."""
    from config import SUPPORTED_LANGUAGES
    return SUPPORTED_LANGUAGES

def validate_language_code(lang_code):
    """Validate if language code is supported."""
    from config import SUPPORTED_LANGUAGES
    return lang_code in SUPPORTED_LANGUAGES.values()
