"""
Internationalization (i18n) — 中英文切换
语言文件: locales/<lang>/locale.json
系统提示: locales/<lang>/system_prompt.txt
"""
import json
import os
from config import LANG

_data = {}


def _load():
    global _data
    if _data:
        return
    path = os.path.join(os.path.dirname(__file__), "..", "locales", LANG, "locale.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _data = json.load(f)
    except FileNotFoundError:
        # fallback to en
        path = os.path.join(os.path.dirname(__file__), "..", "locales", "en", "locale.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                _data = json.load(f)
        except FileNotFoundError:
            _data = {}


def t(key: str, **kwargs) -> str:
    """翻译: t('server_ready') → 当前语言文本"""
    _load()
    msg = _data.get(key, key)
    if kwargs:
        return msg.format(**kwargs)
    return msg


def get_system_prompt() -> str:
    """加载当前语言的系统提示"""
    path = os.path.join(os.path.dirname(__file__), "..", "locales", LANG, "system_prompt.txt")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "You are a knowledge base assistant."
