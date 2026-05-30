"""
Knowledge Graph Enhanced Retriever
通用知识图谱构建与检索增强，不依赖特定领域。
从笔记的 [[双向链接]] 自动构建概念关系网络。
"""
import os
import re
import json
import time
import threading
from typing import Dict, List, Set, Tuple, Optional
from config import VAULT_PATH, TOP_K
from locale import t

# 全局知识图谱缓存
_graph: Dict[str, Dict] = {}
_graph_lock = threading.Lock()
_last_build: float = 0
BUILD_INTERVAL = 300  # 5分钟刷新一次


def _extract_wikilinks(content: str) -> Set[str]:
    """提取 [[wikilinks]] 中的目标概念。"""
    return set(re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content))


def _extract_tags(content: str) -> Set[str]:
    """提取 frontmatter tags。"""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return set()
    tags = set()
    in_tags = False
    for line in match.group(1).split('\n'):
        if line.strip().startswith('tags:'):
            in_tags = True
            # tags: [tag1, tag2] 单行格式
            inline = re.search(r'\[(.+?)\]', line)
            if inline:
                tags.update(t.strip() for t in inline.group(1).split(','))
                in_tags = False
            continue
        if in_tags:
            if line.strip().startswith('- '):
                tags.add(line.strip()[2:].strip().strip('"').strip("'"))
            else:
                in_tags = False
    return tags


def _extract_headings(content: str) -> List[str]:
    """提取标题作为子概念。"""
    return [m.group(1).strip() for m in re.finditer(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)]


def build_graph(vault_path: str = VAULT_PATH) -> Dict[str, Dict]:
    """扫描 vault 构建通用知识图谱。"""
    graph = {}
    skip_dirs = {'.obsidian', '.update_backup', '.git', 'node_modules', 'kb-backend', 'kb-plugin'}

    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            concept = fname.replace('.md', '')
            rel_path = os.path.relpath(fpath, vault_path).replace('\\', '/')

            # 提取元信息
            links = _extract_wikilinks(content)
            tags = _extract_tags(content)
            headings = _extract_headings(content)

            graph[concept] = {
                'path': rel_path,
                'links_to': list(links),
                'tags': list(tags),
                'headings': headings[:10],  # 最多10个标题
                'size': len(content),
            }

    # 构建反向链接
    for name, data in graph.items():
        data['linked_from'] = [
            n for n, d in graph.items()
            if name in d['links_to'] and n != name
        ]

    # 计算连接度
    for name, data in graph.items():
        data['connectivity'] = len(data['links_to']) + len(data['linked_from'])

    return graph


def get_graph(force_rebuild: bool = False) -> Dict[str, Dict]:
    """获取知识图谱（带缓存）。"""
    global _graph, _last_build
    with _graph_lock:
        now = time.time()
        if force_rebuild or not _graph or (now - _last_build > BUILD_INTERVAL):
            _graph = build_graph()
            _last_build = now
            print(f"[KG] {t('graph_built', count=len(_graph))}", flush=True)
        return _graph


def find_related(concept: str, depth: int = 1, max_results: int = 10) -> List[Dict]:
    """查找与概念相关的所有节点。"""
    graph = get_graph()
    if concept not in graph:
        # 模糊匹配
        matches = [n for n in graph if concept.lower() in n.lower()]
        if not matches:
            return []
        concept = matches[0]

    visited = set()
    results = []

    def traverse(name: str, d: int):
        if d > depth or name in visited or len(results) >= max_results:
            return
        visited.add(name)
        if name in graph:
            data = graph[name]
            results.append({
                'name': name,
                'path': data['path'],
                'connectivity': data['connectivity'],
                'depth': d,
            })
            # 按连接度排序遍历
            related = sorted(
                [(n, graph[n]['connectivity']) for n in data['links_to'] + data['linked_from']
                 if n in graph and n not in visited],
                key=lambda x: x[1], reverse=True
            )
            for n, _ in related[:5]:  # 每层最多5个
                traverse(n, d + 1)

    traverse(concept, 0)
    return results


def get_context_for_query(query: str, top_k: int = 3) -> str:
    """根据查询从知识图谱提取相关上下文。"""
    graph = get_graph()
    if not graph:
        return ""

    # 从查询中提取可能的概念词
    query_lower = query.lower()
    matched = []
    for name, data in graph.items():
        score = 0
        if name.lower() in query_lower:
            score += 10  # 精确匹配
        elif any(name.lower() in w for w in query_lower.split()):
            score += 5   # 部分匹配
        if score > 0:
            matched.append((name, score + data['connectivity']))

    if not matched:
        return ""

    matched.sort(key=lambda x: x[1], reverse=True)

    # 构建上下文
    context_parts = []
    for name, _ in matched[:top_k]:
        data = graph[name]
        # 获取直接关联的概念
        related = [n for n in data['links_to'] + data['linked_from'] if n in graph][:5]
        if related:
            context_parts.append(f"概念「{name}」关联: {', '.join(related)}")

    return "\n".join(context_parts) if context_parts else ""


def get_graph_stats() -> Dict:
    """获取图谱统计信息。"""
    graph = get_graph()

    # 按连接度排序
    by_connectivity = sorted(graph.items(), key=lambda x: x[1]['connectivity'], reverse=True)

    # 统计标签
    all_tags = {}
    for data in graph.values():
        for tag in data['tags']:
            all_tags[tag] = all_tags.get(tag, 0) + 1

    return {
        'total_concepts': len(graph),
        'total_links': sum(len(d['links_to']) for d in graph.values()),
        'most_connected': [
            {'name': name, 'connectivity': data['connectivity']}
            for name, data in by_connectivity[:10]
        ],
        'top_tags': dict(sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:20]),
    }
