"""
CRISPRoff dedicated knowledge base.
Auto-collects and organizes all CRISPRoff-related content.
"""
import os
import time
from typing import Dict, List
from config import VAULT_PATH
from vectorstore import collection

CRISPROFF_DIR = os.path.join(VAULT_PATH, "02_知识加工区", "概念卡片")
CRISPROFF_INDEX = os.path.join(VAULT_PATH, "00_系统", "CRISPRoff知识库索引.md")


def scan_crisproff_content() -> Dict[str, List[Dict]]:
    """Scan vault for all CRISPRoff-related content."""
    categories = {
        "概念卡片": [],
        "实验方法": [],
        "文献笔记": [],
        "载体信息": [],
        "sgRNA设计": [],
        "其他": [],
    }

    # Get all documents from ChromaDB
    try:
        all_docs = collection.get(include=["metadatas", "documents"])
    except Exception as e:
        print(f"[CRISPROFF] Error getting docs: {e}", flush=True)
        return categories

    if not all_docs or not all_docs["ids"]:
        return categories

    # Scan for CRISPRoff-related content
    for i, meta in enumerate(all_docs["metadatas"]):
        title = meta.get("title", "").lower()
        tags = meta.get("tags", "").lower()
        aliases = meta.get("aliases", "").lower()
        source = meta.get("source", "")
        text = all_docs["documents"][i].lower()

        # Check if related to CRISPRoff
        is_crisproff = any([
            "crisproff" in title,
            "crisproff" in tags,
            "crisproff" in aliases,
            "crisproff" in text[:500],
            "crisproff" in source.lower(),
        ])

        if not is_crisproff:
            continue

        # Categorize
        entry = {
            "id": all_docs["ids"][i],
            "title": meta.get("title", ""),
            "source": source,
            "preview": all_docs["documents"][i][:200],
        }

        if "02_知识加工区/概念卡片" in source:
            categories["概念卡片"].append(entry)
        elif "02_知识加工区/实验方法库" in source:
            categories["实验方法"].append(entry)
        elif "01_输入区/文献笔记" in source:
            categories["文献笔记"].append(entry)
        elif "载体" in title or "vector" in tags:
            categories["载体信息"].append(entry)
        elif "sgrna" in title or "sgrna" in tags:
            categories["sgRNA设计"].append(entry)
        else:
            categories["其他"].append(entry)

    return categories


def generate_crisproff_index() -> str:
    """Generate CRISPRoff knowledge base index."""
    categories = scan_crisproff_content()

    total = sum(len(v) for v in categories.values())

    # Build index content
    sections = []
    for cat, entries in categories.items():
        if not entries:
            continue
        section = f"\n### {cat} ({len(entries)})\n"
        # Deduplicate by source
        seen = set()
        for e in entries:
            if e["source"] not in seen:
                seen.add(e["source"])
                section += f"- [[{e['source']}|{e['title']}]]\n"
        sections.append(section)

    index_content = f"""# CRISPRoff 专属知识库索引

> 此文件由知识库助手自动维护，最后更新：{time.strftime("%Y-%m-%d %H:%M:%S")}

## 概述

CRISPRoff 是一种多层基因沉默系统，通过 dCas9 融合 ZNF-KRAB 和 DNMT3A/DNMT3L 实现持久的基因沉默。

本索引汇总了知识库中所有与 CRISPRoff 相关的内容，共 **{total}** 条记录。

## 核心概念

- [[CRISPRoff]] - CRISPRoff 系统概述
- [[dCas9]] - 催化失活的 Cas9
- [[ZNF-KRAB]] - KRAB 转录抑制结构域
- [[DNMT3A - DNMT3L]] - DNA 甲基转移酶
- [[KRAB-KAP1-SETDB1通路]] - 异染色质形成通路
- [[表观遗传记忆]] - 表观遗传记忆机制

## 知识库内容
{"".join(sections)}

## 相关技术

- [[sgRNA设计规则]] - sgRNA 设计指南
- [[AAV载体递送]] - AAV 递送方案
- [[mRNA递送]] - mRNA/LNP 递送
- [[BSP测序]] - 甲基化验证方法
- [[WGBS]] - 全基因组甲基化测序

## 使用建议

1. 查阅 [[CRISPRoff]] 了解系统概述
2. 查看实验方法了解具体操作方案
3. 参考文献笔记了解最新研究进展
4. 使用问答功能查询具体问题
"""

    return index_content


def save_crisproff_index() -> str:
    """Save CRISPRoff knowledge base index."""
    content = generate_crisproff_index()

    with open(CRISPROFF_INDEX, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[CRISPROFF] Index saved", flush=True)
    return CRISPROFF_INDEX


def get_crisproff_stats() -> Dict:
    """Get CRISPRoff knowledge base statistics."""
    categories = scan_crisproff_content()
    return {
        "total": sum(len(v) for v in categories.values()),
        "categories": {cat: len(entries) for cat, entries in categories.items() if entries},
    }
