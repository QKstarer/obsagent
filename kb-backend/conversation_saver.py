"""
Auto-save conversations to Obsidian vault.
"""
import os
import time
from typing import List, Dict
from config import VAULT_PATH

CONVERSATION_DIR = os.path.join(VAULT_PATH, "01_输入区", "对话记录")

# Ensure directory exists
os.makedirs(CONVERSATION_DIR, exist_ok=True)


def save_conversation(query: str, answer: str, sources: List[Dict]) -> str:
    """Save a Q&A conversation to the vault."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    date_str = time.strftime("%Y-%m-%d")

    # Generate filename from query (first 30 chars)
    safe_query = query[:30].replace("/", "_").replace("\\", "_").replace(":", "_")
    safe_query = "".join(c for c in safe_query if c.isalnum() or c in " _-_" or '一' <= c <= '鿿')
    safe_query = safe_query.strip() or "对话"
    filename = f"{date_str}_{safe_query}.md"
    filepath = os.path.join(CONVERSATION_DIR, filename)

    # Build source references
    source_refs = ""
    if sources:
        source_refs = "\n## 参考来源\n"
        for s in sources[:5]:
            title = s.get("title", "")
            source = s.get("source", "")
            score = s.get("score", 0)
            source_refs += f"- [[{source}|{title}]] (相关度: {score:.0%})\n"

    # Build markdown content
    content = f"""---
ai_processed: false
date: {date_str}
tags:
  - 对话记录
  - AI问答
type: conversation
---

# {query}

> 对话时间：{timestamp}

## 问题

{query}

## 回答

{answer}
{source_refs}
---
*此对话由知识库助手自动保存*
"""

    # Write file (append if exists)
    mode = "a" if os.path.exists(filepath) else "w"
    with open(filepath, mode, encoding="utf-8") as f:
        if mode == "a":
            f.write(f"\n\n---\n\n{content}")
        else:
            f.write(content)

    print(f"[CONVERSATION] Saved: {filename}", flush=True)
    return filepath


def get_conversation_stats() -> Dict:
    """Get conversation statistics."""
    if not os.path.exists(CONVERSATION_DIR):
        return {"total": 0, "today": 0}

    files = [f for f in os.listdir(CONVERSATION_DIR) if f.endswith(".md")]
    today = time.strftime("%Y-%m-%d")
    today_files = [f for f in files if f.startswith(today)]

    return {
        "total": len(files),
        "today": len(today_files),
    }
