import httpx
import threading
import time
from typing import List
from concurrent.futures import ThreadPoolExecutor
from config import OLLAMA_BASE, OLLAMA_EMBED

embed_progress = {"done": 0, "total": 0, "running": False}


def _embedding_ollama(text: str) -> List[float]:
    with httpx.Client(timeout=60) as client:
        resp = client.post(f"{OLLAMA_BASE}/api/embeddings", json={
            "model": OLLAMA_EMBED,
            "prompt": text
        })
        resp.raise_for_status()
        return resp.json()["embedding"]


def get_embedding_sync(text: str) -> List[float]:
    return _embedding_ollama(text)


def get_embeddings_batch_sync(texts: List[str]) -> List[List[float]]:
    global embed_progress
    results = [None] * len(texts)
    embed_progress = {"done": 0, "total": len(texts), "running": True}
    lock = threading.Lock()

    def _task(idx):
        results[idx] = _embedding_ollama(texts[idx])
        with lock:
            embed_progress["done"] += 1
            d = embed_progress["done"]
            t = embed_progress["total"]
            if d % 10 == 0 or d == t:
                print(f"  [EMBED] {d}/{t} ({d*100//t}%)", flush=True)

    # Use 2 workers - Ollama CPU handles ~1 concurrent request well
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_task, i) for i in range(len(texts))]
        for f in futures:
            f.result()

    embed_progress["running"] = False
    print(f"  [EMBED] ALL DONE: {len(texts)} chunks", flush=True)
    return results


async def get_embedding(text: str) -> List[float]:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{OLLAMA_BASE}/api/embeddings", json={
            "model": OLLAMA_EMBED,
            "prompt": text
        })
        resp.raise_for_status()
        return resp.json()["embedding"]


async def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    import asyncio
    semaphore = asyncio.Semaphore(4)  # Limit concurrent requests

    async def _limited(text):
        async with semaphore:
            return await get_embedding(text)

    return await asyncio.gather(*[_limited(t) for t in texts])
