from deep_translator import GoogleTranslator

async def translate_message(text, from_lang, to_lang):
    if from_lang == to_lang:
        return text
    try:
        translated = GoogleTranslator(source=from_lang, target=to_lang).translate(text)
        return translated
    except Exception:
        return text
