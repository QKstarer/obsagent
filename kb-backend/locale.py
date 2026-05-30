"""
Internationalization (i18n) — 中英文切换
语言文件存储在 locales/<lang>/locale.json
"""
import json
import os
from config import LANG

_locales = {}


def _load_locale(lang: str):
    """加载语言文件。"""
    locale_path = os.path.join(
        os.path.dirname(__file__), "..", "locales", lang, "locale.json"
    )
    try:
        with open(locale_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[LOCALE] Warning: {locale_path} not found, falling back to en", flush=True)
        return {}


def _get_locale():
    """获取当前语言的翻译字典。"""
    global _locales
    if not _locales:
        _locales = _load_locale(LANG)
        if not _locales:
            _locales = _load_locale("en")
    return _locales


def t(key: str, **kwargs) -> str:
    """翻译函数: t('server_ready') → 当前语言的文本"""
    locale = _get_locale()
    msg = locale.get(key, key)
    if kwargs:
        return msg.format(**kwargs)
    return msg


def get_lang() -> str:
    """获取当前语言代码。"""
    return LANG
