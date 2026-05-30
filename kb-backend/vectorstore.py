import os
import re
import shutil
import threading
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Set
from config import CHROMA_PATH
from embeddings import get_embedding_sync, get_embeddings_batch_sync, get_embedding

# In-memory keyword index: keyword -> set of doc IDs
_keyword_index: Dict[str, Set[str]] = {}
# Doc metadata cache: doc_id -> {title, tags, aliases, source}
_doc_meta_cache: Dict[str, Dict[str, str]] = {}
_index_lock = threading.Lock()


def _init_chromadb():
    """Initialize ChromaDB with auto-recovery on corruption."""
    global client, collection
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(
            name="obsidian_kb",
            metadata={"hnsw:space": "cosine"}
        )
        # Test if collection is usable
        collection.count()
        print(f"[VECTORSTORE] ChromaDB loaded from {CHROMA_PATH}", flush=True)
    except Exception as e:
        print(f"[VECTORSTORE] ChromaDB corrupted ({e}), rebuilding...", flush=True)
        # Delete corrupted data and recreate
        try:
            client.delete_collection("obsidian_kb")
        except Exception:
            pass
        if os.path.exists(CHROMA_PATH):
            shutil.rmtree(CHROMA_PATH, ignore_errors=True)
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(
            name="obsidian_kb",
            metadata={"hnsw:space": "cosine"}
        )
        print("[VECTORSTORE] ChromaDB recreated (empty)", flush=True)


# Initialize on module load
client = None
collection = None
_init_chromadb()


def _tokenize(text: str) -> List[str]:
    """Split text into searchable tokens (lowercase)."""
    if not text:
        return []
    text = text.lower()
    # Split on whitespace, punctuation, Chinese particles
    tokens = re.split(r'[\s,，、?？!！.。;；:：的了呢吗吧啊呀哦\-_/\\]+', text)
    return [t for t in tokens if len(t) >= 2]


def _index_doc(doc_id: str, metadata: Dict[str, str]):
    """Add a document to the keyword index."""
    title = metadata.get("title", "")
    tags = metadata.get("tags", "")
    aliases = metadata.get("aliases", "")
    source = metadata.get("source", "")

    _doc_meta_cache[doc_id] = {
        "title": title,
        "tags": tags,
        "aliases": aliases,
        "source": source,
    }

    # Index title, tags, aliases, and source
    all_text = f"{title} {tags} {aliases} {source}"
    tokens = _tokenize(all_text)
    # Also index full title as a token for exact-ish matching
    if title:
        tokens.append(title.lower())

    for token in set(tokens):
        if token not in _keyword_index:
            _keyword_index[token] = set()
        _keyword_index[token].add(doc_id)


def _deindex_doc(doc_id: str):
    """Remove a document from the keyword index."""
    if doc_id in _doc_meta_cache:
        del _doc_meta_cache[doc_id]
    # Remove from all keyword entries
    to_remove = []
    for keyword, ids in _keyword_index.items():
        ids.discard(doc_id)
        if not ids:
            to_remove.append(keyword)
    for k in to_remove:
        del _keyword_index[k]


def rebuild_keyword_index():
    """Rebuild the entire keyword index from ChromaDB. Called on startup."""
    global _keyword_index, _doc_meta_cache
    if collection is None:
        print("[VECTORSTORE] Cannot rebuild index: collection not initialized", flush=True)
        return
    with _index_lock:
        _keyword_index = {}
        _doc_meta_cache = {}

        offset = 0
        batch_size = 1000
        while True:
            try:
                result = collection.get(
                    include=["metadatas"],
                    offset=offset,
                    limit=batch_size,
                )
            except Exception as e:
                print(f"[VECTORSTORE] Error reading batch at offset {offset}: {e}", flush=True)
                break
            if not result["ids"]:
                break
            for i, doc_id in enumerate(result["ids"]):
                _index_doc(doc_id, result["metadatas"][i])
            offset += len(result["ids"])
            if len(result["ids"]) < batch_size:
                break

    print(f"[VECTORSTORE] Keyword index rebuilt: {len(_doc_meta_cache)} docs indexed", flush=True)


def keyword_search(query_text: str, top_k: int = 10) -> List[Dict]:
    """Search using the in-memory keyword index. Returns doc IDs and metadata."""
    tokens = _tokenize(query_text)
    if not tokens:
        return []

    with _index_lock:
        # Find docs matching any token
        candidate_ids: Dict[str, int] = {}  # doc_id -> match count
        for token in tokens:
            # Exact match
            if token in _keyword_index:
                for doc_id in _keyword_index[token]:
                    candidate_ids[doc_id] = candidate_ids.get(doc_id, 0) + 2
            # Prefix match for longer tokens
            if len(token) >= 3:
                for keyword, ids in _keyword_index.items():
                    if keyword.startswith(token) and keyword != token:
                        for doc_id in ids:
                            candidate_ids[doc_id] = candidate_ids.get(doc_id, 0) + 1

        # Sort by match count (descending)
        sorted_candidates = sorted(candidate_ids.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_candidates[:top_k]:
            meta = _doc_meta_cache.get(doc_id, {})
            results.append({
                "id": doc_id,
                "metadata": meta,
                "keyword_score": score,
            })
        return results


def add_documents(documents: List[Dict]) -> int:
    if not documents:
        return 0
    ids = [d["id"] for d in documents]
    texts = [d["text"] for d in documents]
    metadatas = []
    for d in documents:
        m = {}
        for k, v in d["metadata"].items():
            if isinstance(v, (str, int, float, bool)):
                m[k] = v
        metadatas.append(m)
    embeddings = get_embeddings_batch_sync(texts)
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_texts = texts[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_embs = embeddings[i:i+batch_size]
        collection.upsert(
            ids=batch_ids,
            documents=batch_texts,
            embeddings=batch_embs,
            metadatas=batch_metas
        )

    # Update keyword index
    with _index_lock:
        for doc_id, meta in zip(ids, metadatas):
            _index_doc(doc_id, meta)

    return len(ids)


def query(text: str, n_results: int = 5) -> List[Dict]:
    embedding = get_embedding_sync(text)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    output = []
    for i in range(len(results["ids"][0])):
        output.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    return output


def remove_by_source(source: str):
    existing = collection.get(where={"source": source})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        # Update keyword index
        with _index_lock:
            for doc_id in existing["ids"]:
                _deindex_doc(doc_id)


def get_stats() -> Dict:
    try:
        count = collection.count()
    except Exception as e:
        print(f"[VECTORSTORE] get_stats error: {e}", flush=True)
        return {"total_chunks": 0, "error": str(e)}
    return {"total_chunks": count}


def clear_all():
    client.delete_collection("obsidian_kb")
    global collection
    collection = client.get_or_create_collection(
        name="obsidian_kb",
        metadata={"hnsw:space": "cosine"}
    )
    with _index_lock:
        _keyword_index.clear()
        _doc_meta_cache.clear()
