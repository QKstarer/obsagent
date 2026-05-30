"""
Knowledge Cache
高频问答对和概念定义缓存，加速常见问题响应。
"""
import os
import json
import time
import threading
from typing import Dict, List, Optional
from config import CHROMA_PATH
from locale import t

CACHE_FILE = os.path.join(CHROMA_PATH, "knowledge_cache.json")
MAX_CACHE_SIZE = 500
CACHE_EXPIRE = 86400 * 7  # 7天过期

_cache: Dict = {}
_lock = threading.Lock()


def _load_cache():
    """从磁盘加载缓存。"""
    global _cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}


def _save_cache():
    """保存缓存到磁盘。"""
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[CACHE] Save error: {e}", flush=True)


def get_cached_answer(query: str) -> Optional[Dict]:
    """查找缓存的答案。"""
    with _lock:
        if not _cache:
            _load_cache()

        # 精确匹配
        if query in _cache:
            entry = _cache[query]
            if time.time() - entry.get('time', 0) < CACHE_EXPIRE:
                entry['hits'] = entry.get('hits', 0) + 1
                _save_cache()
                return entry
            else:
                del _cache[query]

        # 模糊匹配（查询包含缓存key）
        query_lower = query.lower().strip()
        for key, entry in _cache.items():
            if time.time() - entry.get('time', 0) >= CACHE_EXPIRE:
                continue
            if key.lower() in query_lower or query_lower in key.lower():
                entry['hits'] = entry.get('hits', 0) + 1
                _save_cache()
                return entry

    return None


def cache_answer(query: str, answer: str, sources: List[Dict] = None):
    """缓存一个问答对。"""
    with _lock:
        if not _cache:
            _load_cache()

        # 缓存满时清理低频条目
        if len(_cache) >= MAX_CACHE_SIZE:
            _cleanup_cache()

        _cache[query] = {
            'answer': answer,
            'sources': sources or [],
            'time': time.time(),
            'hits': 1,
        }
        _save_cache()


def _cleanup_cache():
    """清理过期和低频缓存。"""
    now = time.time()
    # 先删过期
    expired = [k for k, v in _cache.items() if now - v.get('time', 0) >= CACHE_EXPIRE]
    for k in expired:
        del _cache[k]

    # 还是太多，删低频
    if len(_cache) >= MAX_CACHE_SIZE:
        sorted_items = sorted(_cache.items(), key=lambda x: x[1].get('hits', 0))
        for k, _ in sorted_items[:len(_cache) // 4]:
            del _cache[k]


def get_cache_stats() -> Dict:
    """缓存统计信息。"""
    with _lock:
        if not _cache:
            _load_cache()

        total_hits = sum(v.get('hits', 0) for v in _cache.values())
        return {
            'cached_queries': len(_cache),
            'total_hits': total_hits,
            'max_size': MAX_CACHE_SIZE,
        }


def clear_cache():
    """清空缓存。"""
    global _cache
    with _lock:
        _cache = {}
        _save_cache()
