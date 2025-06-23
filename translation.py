from deep_translator import GoogleTranslator

def translate_message(text, src_lang, dest_lang):
    try:
        return GoogleTranslator(source=src_lang, target=dest_lang).translate(text)
    except Exception:
        return text  # fallback: return original
