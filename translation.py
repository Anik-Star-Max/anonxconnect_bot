from deep_translator import GoogleTranslator
from database import get_user, is_vip
import logging

logger = logging.getLogger(__name__)

def detect_language(text: str) -> str:
    """Detect the language of the text."""
    try:
        # Use Google Translator to detect language
        detected = GoogleTranslator(source='auto', target='en').translate(text)
        # This is a simplified detection, in real implementation you'd use language detection
        return 'auto'
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return 'en'

def translate_message(text: str, target_language: str, source_language: str = 'auto') -> str:
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

def should_translate(sender_id: int, receiver_id: int) -> tuple:
    """Check if message should be translated and return languages."""
    sender = get_user(sender_id)
    receiver = get_user(receiver_id)
    
    # Only VIP users can use translation
    if not is_vip(receiver_id):
        return False, None, None
    
    # Check if receiver has translation enabled
    if not receiver.get('translation_enabled', False):
        return False, None, None
    
    sender_lang = sender.get('language', 'en')
    receiver_lang = receiver.get('language', 'en')
    
    # No need to translate if same language
    if sender_lang == receiver_lang:
        return False, None, None
    
    return True, sender_lang, receiver_lang

def format_translated_message(original: str, translated: str, source_lang: str) -> str:
    """Format message with translation indicator."""
    return f"🌐 **Translated from {source_lang.upper()}:**\n{translated}\n\n💬 **Original:**\n{original}"

def get_language_name(code: str) -> str:
    """Get language name from code."""
    languages = {
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
    return languages.get(code, code.upper())
