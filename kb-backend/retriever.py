import re
from typing import List, Dict
from vectorstore import query, keyword_search, collection
from config import TOP_K

# Question patterns to strip for keyword matching
QUESTION_PREFIX = re.compile(r'^(什么是|请介绍|请解释|帮我查|告诉我|讲讲|说说|聊聊)')
QUESTION_SUFFIX = re.compile(r'(是什么|是怎么回事|怎么样|怎么办|如何|是什么意思|指的是|的原理|的机制|的介绍|简介)$')


def _extract_search_terms(query_text: str) -> List[str]:
    """Extract searchable terms from a query like 'CRISPRoff是什么' -> ['crisproff']."""
    q = query_text.lower().strip()
    # Strip question prefixes and suffixes
    q = QUESTION_PREFIX.sub('', q).strip()
    q = QUESTION_SUFFIX.sub('', q).strip()
    # Split on whitespace, punctuation, Chinese particles, and question words
    terms = re.split(r'[\s,，、?？!！.。;；:：的了呢吗吧啊呀哦怎么什么如何]+', q)
    # Filter out very short terms
    return [t for t in terms if len(t) >= 2]


def search(query_text: str, top_k: int = TOP_K) -> List[Dict]:
    # Embedding search
    emb_results = query(query_text, n_results=top_k)

    # Keyword search using in-memory index (no full ChromaDB scan)
    kw_results = []
    try:
        terms = _extract_search_terms(query_text)
        if terms:
            search_text = " ".join(terms)
            kw_hits = keyword_search(search_text, top_k=top_k * 2)
            for hit in kw_hits:
                # Fetch full text from ChromaDB for matched docs
                doc = collection.get(
                    ids=[hit["id"]],
                    include=["documents", "metadatas"]
                )
                if doc["ids"]:
                    kw_results.append({
                        "id": doc["ids"][0],
                        "text": doc["documents"][0],
                        "metadata": doc["metadatas"][0],
                        "distance": 0.01  # High relevance for keyword match
                    })
    except Exception as e:
        print(f"[SEARCH] Keyword search error: {e}", flush=True)

    # Merge: keyword hits first, then embedding results
    seen = set()
    merged = []
    for r in kw_results + emb_results:
        if r["id"] not in seen:
            seen.add(r["id"])
            merged.append(r)
    return merged[:top_k]


def build_context(results: List[Dict]) -> str:
    if not results:
        return "未找到相关知识。"
    parts = []
    for i, r in enumerate(results):
        meta = r["metadata"]
        source = meta.get("source", "未知")
        title = meta.get("title", "")
        parts.append(f"[来源 {i+1}: {title} ({source})]\n{r['text']}")
    return "\n\n---\n\n".join(parts)


def retrieve_for_chat(query_text: str) -> Dict:
    results = search(query_text)
    context = build_context(results)
    sources = []
    for r in results:
        meta = r["metadata"]
        sources.append({
            "title": meta.get("title", ""),
            "source": meta.get("source", ""),
            "score": round(1 - r["distance"], 4),
            "preview": r["text"][:100]
        })
    return {"context": context, "sources": sources}
