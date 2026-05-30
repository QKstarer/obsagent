"""
Knowledge Graph Enhanced Retriever
通用知识图谱，增量更新，不依赖特定领域。
从笔记的 [[双向链接]] 自动构建概念关系网络。
"""
import os
import re
import time
import threading
from typing import Dict, List, Set
from config import VAULT_PATH, TOP_K
from locale import t

# 全局状态
_graph: Dict[str, Dict] = {}
_graph_lock = threading.Lock()
_file_mtimes: Dict[str, float] = {}  # 路径 → 修改时间
_dirty = True  # 标记需要更新
CHECK_INTERVAL = 30  # 每30秒检查文件变更

skip_dirs = {'.obsidian', '.update_backup', '.git', 'node_modules', 'kb-backend', 'kb-plugin'}


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


def _parse_file(fpath: str, vault_path: str) -> Dict:
    """解析单个文件。"""
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return None

    concept = os.path.basename(fpath).replace('.md', '')
    rel_path = os.path.relpath(fpath, vault_path).replace('\\', '/')
    links = _extract_wikilinks(content)
    tags = _extract_tags(content)

    return {
        'path': rel_path,
        'links_to': list(links),
        'tags': list(tags),
        'size': len(content),
    }


def _check_dirty() -> List[str]:
    """检查哪些文件有变更，返回变更文件列表。"""
    global _file_mtimes, _dirty
    changed = []

    current_files = {}
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                mtime = os.path.getmtime(fpath)
            except OSError:
                continue
            current_files[fpath] = mtime

            old_mtime = _file_mtimes.get(fpath, 0)
            if mtime > old_mtime:
                changed.append(fpath)

    # 检查删除的文件
    deleted = set(_file_mtimes.keys()) - set(current_files.keys())
    for fpath in deleted:
        changed.append(fpath)  # 用空内容标记删除

    _file_mtimes = current_files
    if changed:
        _dirty = True

    return changed


def _apply_changes(changed_files: List[str]):
    """增量更新：只处理变更的文件。"""
    global _graph
    with _graph_lock:
        for fpath in changed_files:
            concept = os.path.basename(fpath).replace('.md', '')

            if not os.path.exists(fpath):
                # 文件已删除
                if concept in _graph:
                    del _graph[concept]
                continue

            data = _parse_file(fpath, VAULT_PATH)
            if data:
                _graph[concept] = data

        # 重建反向链接（只扫全量一次）
        for name, data in _graph.items():
            data['linked_from'] = [
                n for n, d in _graph.items()
                if name in d['links_to'] and n != name
            ]
            data['connectivity'] = len(data['links_to']) + len(data['linked_from'])


def _full_build():
    """首次全量构建。"""
    global _graph, _file_mtimes, _dirty
    _graph = {}
    _file_mtimes = {}

    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fpath = os.path.join(root, fname)
            try:
                mtime = os.path.getmtime(fpath)
                _file_mtimes[fpath] = mtime
            except OSError:
                continue

            data = _parse_file(fpath, VAULT_PATH)
            if data:
                concept = fname.replace('.md', '')
                _graph[concept] = data

    # 构建反向链接
    for name, data in _graph.items():
        data['linked_from'] = [
            n for n, d in _graph.items()
            if name in d['links_to'] and n != name
        ]
        data['connectivity'] = len(data['links_to']) + len(data['linked_from'])

    _dirty = False
    print(f"[KG] {t('graph_built', count=len(_graph))}", flush=True)


def _background_check():
    """后台线程：定期检查文件变更，增量更新。"""
    while True:
        time.sleep(CHECK_INTERVAL)
        try:
            changed = _check_dirty()
            if changed:
                _apply_changes(changed)
                print(f"[KG] Incremental update: {len(changed)} files", flush=True)
        except Exception as e:
            print(f"[KG] Check error: {e}", flush=True)


# 启动后台检查线程
_checker = threading.Thread(target=_background_check, daemon=True)
_checker.start()


def get_graph(force_rebuild: bool = False) -> Dict[str, Dict]:
    """获取知识图谱（带增量缓存）。"""
    global _dirty
    with _graph_lock:
        if force_rebuild or _dirty or not _graph:
            _full_build()
        return _graph


def find_related(concept: str, depth: int = 1, max_results: int = 10) -> List[Dict]:
    """查找与概念相关的所有节点。"""
    graph = get_graph()
    if concept not in graph:
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
            related = sorted(
                [(n, graph[n]['connectivity']) for n in data['links_to'] + data['linked_from']
                 if n in graph and n not in visited],
                key=lambda x: x[1], reverse=True
            )
            for n, _ in related[:5]:
                traverse(n, d + 1)

    traverse(concept, 0)
    return results


def get_context_for_query(query: str, top_k: int = 3) -> str:
    """根据查询从知识图谱提取相关上下文。"""
    graph = get_graph()
    if not graph:
        return ""

    query_lower = query.lower()
    matched = []
    for name, data in graph.items():
        score = 0
        if name.lower() in query_lower:
            score += 10
        elif any(name.lower() in w for w in query_lower.split()):
            score += 5
        if score > 0:
            matched.append((name, score + data['connectivity']))

    if not matched:
        return ""

    matched.sort(key=lambda x: x[1], reverse=True)

    context_parts = []
    for name, _ in matched[:top_k]:
        data = graph[name]
        related = [n for n in data['links_to'] + data['linked_from'] if n in graph][:5]
        if related:
            context_parts.append(f"概念「{name}」关联: {', '.join(related)}")

    return "\n".join(context_parts) if context_parts else ""


def get_graph_stats() -> Dict:
    """获取图谱统计信息。"""
    graph = get_graph()
    by_connectivity = sorted(graph.items(), key=lambda x: x[1]['connectivity'], reverse=True)

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
