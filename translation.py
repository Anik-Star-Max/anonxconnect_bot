from deep_translator import GoogleTranslator

def translate_text(text, source_lang, target_lang):
    try:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except:
        return text

def translate_message(text, from_lang, to_lang):
    if from_lang == to_lang:
        return text
    return translate_text(text, from_lang, to_lang)
