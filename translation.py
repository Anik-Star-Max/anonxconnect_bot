from deep_translator import GoogleTranslator
import config

def translate_message(text, source_lang, target_lang):
    if source_lang == target_lang:
        return text
    
    try:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except:
        return text

def get_language_name(lang_code):
    return config.SUPPORTED_LANGUAGES.get(lang_code, lang_code)
