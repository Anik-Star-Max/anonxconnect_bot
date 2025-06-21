from deep_translator import GoogleTranslator

def translate_text(text, source='auto', target='en'):
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except:
        return text

def translate_message(text, source_lang, target_lang):
    if source_lang == target_lang:
        return text
    return translate_text(text, source_lang, target_lang)
