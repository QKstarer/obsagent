"""
Internationalization (i18n) — 中英文切换
启动时加载一次，后续走内存缓存
"""
import json
import os
from config import LANG

_data = None
_prompt = None


def _load_all():
    """启动时调用一次，加载语言包和系统提示。"""
    global _data, _prompt
    base = os.path.join(os.path.dirname(__file__), "..", "locales", LANG)

    # 加载翻译字典
    locale_path = os.path.join(base, "locale.json")
    try:
        with open(locale_path, "r", encoding="utf-8") as f:
            _data = json.load(f)
    except FileNotFoundError:
        fallback = os.path.join(os.path.dirname(__file__), "..", "locales", "en", "locale.json")
        try:
            with open(fallback, "r", encoding="utf-8") as f:
                _data = json.load(f)
        except FileNotFoundError:
            _data = {}

    # 加载系统提示
    prompt_path = os.path.join(base, "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            _prompt = f.read().strip()
    except FileNotFoundError:
        _prompt = "You are a knowledge base assistant."

    print(f"[LOCALE] Loaded: {LANG} ({len(_data)} keys)", flush=True)


def t(key: str, **kwargs) -> str:
    """翻译: t('server_ready') → 当前语言文本"""
    if _data is None:
        _load_all()
    msg = _data.get(key, key)
    if kwargs:
        return msg.format(**kwargs)
    return msg


def get_system_prompt() -> str:
    """获取系统提示（已缓存）"""
    if _prompt is None:
        _load_all()
    return _prompt
