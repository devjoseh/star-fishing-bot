import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")

current_lang = "pt"
translationsCache = {}

def load_language(lang):
    file_path = os.path.join(LOCALES_DIR, f"{lang}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[i18n] Erro carregando {lang}.json: {e}")
    return {}

def set_language(lang):
    global current_lang, translationsCache
    if lang in ["pt", "en"]:
        current_lang = lang
        translationsCache = load_language(lang)
        # Fallback to pt if empty
        if not translationsCache and lang != "pt":
            translationsCache = load_language("pt")

def t(key, **kwargs):
    if not translationsCache:
        set_language(current_lang)
    
    text = translationsCache.get(key, key)
    if kwargs and text != key:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass # ignore missing kwargs
    return text
