"""
Internationalization (i18n) — 中英文切换
设置环境变量 LANG=en 或 LANG=zh 切换语言
"""
from config import LANG

# ─── 日志消息 ───
LOG = {
    "zh": {
        "server_ready": "服务已就绪",
        "vault_empty": "ChromaDB 为空，开始后台索引...",
        "vault_loaded": "ChromaDB 已加载 {count} 个文本块，重建关键词索引...",
        "vault_error": "ChromaDB 初始化错误: {error}，将重新索引",
        "index_start": "开始后台索引...",
        "index_chunks": "发现 {count} 个文本块，生成嵌入向量...",
        "index_done": "索引完成: {count} 个文本块",
        "index_error": "索引错误: {error}",
        "watcher_started": "文件监控已启动",
        "watcher_stopped": "文件监控已停止",
        "watcher_paused": "文件监控已暂停",
        "watcher_resumed": "文件监控已恢复",
        "watcher_skip": "跳过 - 正在索引中",
        "watcher_update": "增量更新 {count} 个文件...",
        "watcher_updated": "已更新: {path} ({count} 个文本块)",
        "watcher_error": "更新 {path} 时出错: {error}",
        "watcher_removed": "已移除: {path}",
        "graph_built": "知识图谱已构建: {count} 个概念",
        "graph_updated": "知识图谱已更新",
        "graph_error": "知识图谱更新出错: {error}",
        "graph_disabled": "图谱自动保存已关闭（设置 GRAPH_SAVE_TO_VAULT=true 启用）",
        "conflict_scan": "开始冲突检测...",
        "conflict_done": "冲突检测完成",
        "cache_hit": "缓存命中: {query}",
        "embed_progress": "[EMBED] {done}/{total} ({percent}%)",
        "embed_done": "[EMBED] 全部完成: {count} 个文本块",
    },
    "en": {
        "server_ready": "Server ready",
        "vault_empty": "ChromaDB empty, starting background indexing...",
        "vault_loaded": "ChromaDB loaded {count} chunks, rebuilding keyword index...",
        "vault_error": "ChromaDB init error: {error}, will re-index",
        "index_start": "Starting background indexing...",
        "index_chunks": "Found {count} chunks, generating embeddings...",
        "index_done": "Indexing done: {count} chunks",
        "index_error": "Indexing error: {error}",
        "watcher_started": "File watcher started",
        "watcher_stopped": "File watcher stopped",
        "watcher_paused": "File watcher paused",
        "watcher_resumed": "File watcher resumed",
        "watcher_skip": "Skipping — indexing in progress",
        "watcher_update": "Incremental update for {count} files...",
        "watcher_updated": "Updated: {path} ({count} chunks)",
        "watcher_error": "Error updating {path}: {error}",
        "watcher_removed": "Removed: {path}",
        "graph_built": "Knowledge graph built: {count} concepts",
        "graph_updated": "Knowledge graph updated",
        "graph_error": "Knowledge graph update error: {error}",
        "graph_disabled": "Graph auto-save disabled (set GRAPH_SAVE_TO_VAULT=true to enable)",
        "conflict_scan": "Starting conflict scan...",
        "conflict_done": "Conflict scan done",
        "cache_hit": "Cache hit: {query}",
        "embed_progress": "[EMBED] {done}/{total} ({percent}%)",
        "embed_done": "[EMBED] All done: {count} chunks",
    },
}


def t(key: str, **kwargs) -> str:
    """翻译函数: t('server_ready') → 当前语言的文本"""
    msg = LOG.get(LANG, LOG["en"]).get(key, key)
    if kwargs:
        return msg.format(**kwargs)
    return msg
