"""
Knowledge graph for Obsidian vault.
Analyzes relationships between concepts, genes, proteins, vectors, and sgRNAs.
"""
import os
import re
import time
from typing import Dict, List, Set, Tuple
from config import VAULT_PATH
from vectorstore import collection

GRAPH_DIR = os.path.join(VAULT_PATH, "00_系统")
GRAPH_FILE = os.path.join(GRAPH_DIR, "知识关联图谱.md")


def extract_links(content: str) -> Set[str]:
    """Extract [[wikilinks]] from content."""
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    return set(re.findall(pattern, content))


def scan_vault_relationships() -> Dict[str, Dict[str, List[str]]]:
    """Scan vault and build relationship graph."""
    relationships = {}

    # Define categories
    categories = {
        "基因": "02_知识加工区/基因实体库",
        "蛋白": "02_知识加工区/蛋白与结构域",
        "载体": "02_知识加工区/载体与质粒",
        "sgRNA": "02_知识加工区/sgRNA数据库",
        "概念": "02_知识加工区/概念卡片",
        "实验方法": "02_知识加工区/实验方法库",
        "学者": "02_知识加工区/学者信息",
    }

    # Scan each category
    for category, path in categories.items():
        full_path = os.path.join(VAULT_PATH, path)
        if not os.path.exists(full_path):
            continue

        for root, dirs, files in os.walk(full_path):
            for fname in files:
                if not fname.endswith('.md') or fname.startswith('模板'):
                    continue

                filepath = os.path.join(root, fname)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    name = fname.replace('.md', '')
                    rel_path = os.path.relpath(filepath, VAULT_PATH).replace("\\", "/")
                    links = extract_links(content)

                    if name not in relationships:
                        relationships[name] = {
                            "category": category,
                            "path": rel_path,
                            "links_to": [],
                            "linked_from": [],
                        }
                    relationships[name]["links_to"] = list(links)

                except Exception as e:
                    print(f"[GRAPH] Error reading {filepath}: {e}", flush=True)

    # Build reverse links
    for name, data in relationships.items():
        for linked in data["links_to"]:
            if linked in relationships:
                if name not in relationships[linked]["linked_from"]:
                    relationships[linked]["linked_from"].append(name)

    return relationships


def find_related_concepts(relationships: Dict, concept: str, depth: int = 2) -> Dict:
    """Find all related concepts up to a certain depth."""
    if concept not in relationships:
        return {"error": f"Concept '{concept}' not found"}

    visited = set()
    result = {"center": concept, "related": []}

    def traverse(name: str, current_depth: int):
        if current_depth > depth or name in visited:
            return
        visited.add(name)

        if name in relationships:
            data = relationships[name]
            result["related"].append({
                "name": name,
                "category": data["category"],
                "path": data["path"],
                "depth": current_depth,
                "link_count": len(data["links_to"]) + len(data["linked_from"]),
            })

            # Traverse links
            for linked in data["links_to"] + data["linked_from"]:
                traverse(linked, current_depth + 1)

    traverse(concept, 0)
    return result


def generate_mermaid_graph(relationships: Dict, center: str, depth: int = 1) -> str:
    """Generate Mermaid diagram for visualization."""
    if center not in relationships:
        return "```mermaid\ngraph TD\n    A[Concept not found]\n```"

    nodes = set()
    edges = []

    def traverse(name: str, current_depth: int):
        if current_depth > depth or name in nodes:
            return
        nodes.add(name)

        if name in relationships:
            data = relationships[name]
            for linked in data["links_to"]:
                if linked in relationships:
                    edges.append(f"    {name} --> {linked}")
                    traverse(linked, current_depth + 1)
            for linked in data["linked_from"]:
                if linked in relationships:
                    edges.append(f"    {linked} --> {name}")
                    traverse(linked, current_depth + 1)

    traverse(center, 0)

    # Build mermaid diagram
    mermaid = "```mermaid\ngraph TD\n"
    for node in nodes:
        if node in relationships:
            cat = relationships[node]["category"]
            mermaid += f"    {node}[{node}<br/>{cat}]\n"
    for edge in edges:
        mermaid += edge + "\n"
    mermaid += "```"

    return mermaid


def generate_knowledge_graph_report(center_concept: str = "CRISPRoff") -> str:
    """Generate a knowledge graph report."""
    relationships = scan_vault_relationships()

    # Find related concepts
    related = find_related_concepts(relationships, center_concept, depth=1)

    # Generate mermaid diagram
    mermaid = generate_mermaid_graph(relationships, center_concept, depth=1)

    # Build report
    date_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # Group by category
    by_category = {}
    for r in related.get("related", []):
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(r)

    sections = []
    for cat, items in by_category.items():
        section = f"\n### {cat}\n"
        for item in sorted(items, key=lambda x: x["link_count"], reverse=True)[:10]:
            section += f"- [[{item['path']}|{item['name']}]] (关联数: {item['link_count']})\n"
        sections.append(section)

    report = f"""# 知识关联图谱 - {center_concept}

> 生成时间：{date_str}
> 关联深度：1 层

## 关联图

{mermaid}

## 关联概念
{"".join(sections)}

## 统计信息

- 中心概念：{center_concept}
- 直接关联：{len(related.get('related', []))} 个
- 关联类别：{len(by_category)} 个

## 使用说明

- 在 Obsidian 中打开此文件可查看可视化图谱
- 点击链接可跳转到相关概念
- 使用 Graph View 可查看完整知识网络
"""

    return report


def save_knowledge_graph(center_concept: str = "CRISPRoff") -> str:
    """Save knowledge graph report."""
    report = generate_knowledge_graph_report(center_concept)

    filepath = os.path.join(GRAPH_DIR, f"知识关联图谱_{center_concept}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[GRAPH] Saved: {filepath}", flush=True)
    return filepath


def get_graph_stats() -> Dict:
    """Get knowledge graph statistics."""
    relationships = scan_vault_relationships()

    categories = {}
    for name, data in relationships.items():
        cat = data["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    # Find most connected concepts
    most_connected = sorted(
        relationships.items(),
        key=lambda x: len(x[1]["links_to"]) + len(x[1]["linked_from"]),
        reverse=True
    )[:10]

    return {
        "total_concepts": len(relationships),
        "categories": categories,
        "most_connected": [
            {
                "name": name,
                "category": data["category"],
                "links": len(data["links_to"]) + len(data["linked_from"]),
            }
            for name, data in most_connected
        ],
    }
