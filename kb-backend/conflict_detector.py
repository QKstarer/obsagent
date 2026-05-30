import json
import time
import asyncio
import threading
from typing import List, Dict, Optional
from vectorstore import collection
from llm import chat_ollama

CONFLICT_PROMPT = """你是一个知识库审查专家。请分析以下两个概念卡片的内容，判断是否存在矛盾或不一致之处。

【概念卡片 A】
标题: {title_a}
内容:
{content_a}

【概念卡片 B】
标题: {title_b}
内容:
{content_b}

请判断：
1. 这两个概念卡片是否存在直接矛盾（对同一事实有不同说法）？
2. 是否存在数据不一致（如数值、参数、阈值不同）？
3. 是否存在模糊或可能引起误解的表述？

请严格按以下 JSON 格式返回（不要添加其他文字）：
{{"has_conflict": true/false, "type": "contradiction/inconsistency/no_conflict", "detail": "具体矛盾描述（如无矛盾则为空字符串）", "suggestion": "建议（如无矛盾则为空字符串）"}}"""

_cache = {
    "report": None,
    "timestamp": 0,
    "running": False,
}
_cache_lock = threading.Lock()

CACHE_TTL = 3600  # 1 hour


def _get_all_concept_cards() -> List[Dict]:
    """Get all concept cards from ChromaDB (files under Cards/Concepts/)."""
    all_docs = collection.get(include=["documents", "metadatas"])
    cards = {}
    for i, meta in enumerate(all_docs["metadatas"]):
        source = meta.get("source", "")
        if not source.startswith("Cards/Concepts/"):
            continue
        if source not in cards:
            cards[source] = {
                "source": source,
                "title": meta.get("title", ""),
                "tags": meta.get("tags", ""),
                "aliases": meta.get("aliases", ""),
                "chunks": [],
            }
        cards[source]["chunks"].append(all_docs["documents"][i])
    return list(cards.values())


# Generic tags that don't indicate specific topic overlap
GENERIC_TAGS = {"concept", "technique", "molecular-biology", "cell-biology", "protein"}
MAX_PAIRS = 50  # Limit total comparisons


def _get_candidate_pairs(cards: List[Dict]) -> List[tuple]:
    """Find pairs of cards that share specific tags, prioritized by overlap count."""
    scored_pairs = []
    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            tags_a = set(cards[i]["tags"].lower().replace(" ", "").split(",")) - GENERIC_TAGS
            tags_b = set(cards[j]["tags"].lower().replace(" ", "").split(",")) - GENERIC_TAGS
            tags_a.discard("")
            tags_b.discard("")
            overlap = tags_a & tags_b
            if overlap:
                # Score by number of shared specific tags
                scored_pairs.append((len(overlap), cards[i], cards[j]))
    # Sort by overlap count (more shared tags = higher priority)
    scored_pairs.sort(reverse=True, key=lambda x: x[0])
    return [(a, b) for _, a, b in scored_pairs[:MAX_PAIRS]]


async def _check_pair(card_a: Dict, card_b: Dict) -> Optional[Dict]:
    """Use LLM to check if two cards have conflicting information."""
    content_a = "\n\n".join(card_a["chunks"])[:1500]
    content_b = "\n\n".join(card_b["chunks"])[:1500]

    prompt = CONFLICT_PROMPT.format(
        title_a=card_a["title"],
        content_a=content_a,
        title_b=card_b["title"],
        content_b=content_b,
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        response = await asyncio.wait_for(chat_ollama(messages), timeout=30)
        response = response.strip()
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response[start:end])
            if result.get("has_conflict"):
                return {
                    "card_a": card_a["source"],
                    "title_a": card_a["title"],
                    "card_b": card_b["source"],
                    "title_b": card_b["title"],
                    "type": result.get("type", "uncertainty"),
                    "detail": result.get("detail", ""),
                    "suggestion": result.get("suggestion", ""),
                }
    except asyncio.TimeoutError:
        print(f"[CONFLICT] Timeout: {card_a['title']} vs {card_b['title']}", flush=True)
    except Exception as e:
        print(f"[CONFLICT] Error: {card_a['title']} vs {card_b['title']}: {e}", flush=True)
    return None


def _scan_sync() -> List[Dict]:
    """Synchronous conflict scan (for background thread)."""
    cards = _get_all_concept_cards()
    print(f"[CONFLICT] Scanning {len(cards)} concept cards...", flush=True)

    pairs = _get_candidate_pairs(cards)
    print(f"[CONFLICT] {len(pairs)} candidate pairs to check (max {MAX_PAIRS})", flush=True)

    conflicts = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for i, (card_a, card_b) in enumerate(pairs):
            try:
                result = loop.run_until_complete(_check_pair(card_a, card_b))
                if result:
                    conflicts.append(result)
                    print(f"[CONFLICT] Found: {card_a['title']} vs {card_b['title']} - {result['type']}", flush=True)
            except Exception as e:
                print(f"[CONFLICT] Error at pair {i}: {e}", flush=True)
            if (i + 1) % 10 == 0:
                print(f"[CONFLICT] Progress: {i+1}/{len(pairs)}", flush=True)
    finally:
        loop.close()

    print(f"[CONFLICT] Scan complete: {len(conflicts)} conflicts found", flush=True)
    return conflicts


def detect_conflicts_background():
    """Background thread entry point for conflict detection."""
    with _cache_lock:
        if _cache["running"]:
            print("[CONFLICT] Scan already running, skipping", flush=True)
            return
        _cache["running"] = True

    try:
        conflicts = _scan_sync()
        with _cache_lock:
            _cache["report"] = {
                "conflicts": conflicts,
                "total_cards": len(_get_all_concept_cards()),
                "total_conflicts": len(conflicts),
                "scanned_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            _cache["timestamp"] = time.time()
    finally:
        with _cache_lock:
            _cache["running"] = False


def get_conflict_report() -> Dict:
    """Get cached conflict report, or trigger a new scan if expired."""
    with _cache_lock:
        if _cache["report"] and (time.time() - _cache["timestamp"] < CACHE_TTL):
            return _cache["report"]
        if _cache["running"]:
            return {"status": "scanning", "message": "冲突扫描正在进行中，请稍后查看"}

    # Trigger background scan
    t = threading.Thread(target=detect_conflicts_background, daemon=True)
    t.start()
    return {"status": "scanning", "message": "已触发冲突扫描，请稍后查看"}


def force_scan() -> Dict:
    """Force a new conflict scan (synchronous, for API endpoint)."""
    with _cache_lock:
        if _cache["running"]:
            return {"status": "scanning", "message": "冲突扫描正在进行中"}

    t = threading.Thread(target=detect_conflicts_background, daemon=True)
    t.start()
    return {"status": "started", "message": "冲突扫描已启动"}
