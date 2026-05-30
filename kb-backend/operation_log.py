"""
Operation log for knowledge base assistant.
Logs all AI operations for audit trail.
Supports log rotation to prevent unlimited growth.
"""
import os
import time
import glob
import threading
from config import VAULT_PATH

LOG_FILE = os.path.join(VAULT_PATH, "00_系统", "操作日志.md")
LOG_DIR = os.path.join(VAULT_PATH, "00_系统")
LOG_PREFIX = "操作日志"
MAX_LOG_SIZE = 1 * 1024 * 1024  # 1MB
MAX_LOG_ARCHIVES = 3
_lock = threading.Lock()


def _ensure_log_file():
    """Ensure the log file exists with header."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("# 操作日志\n\n")
            f.write("> 此文件由知识库助手自动维护，记录所有 AI 操作\n\n")
            f.write("---\n\n")


def _rotate_if_needed():
    """Rotate log file if it exceeds max size."""
    try:
        if not os.path.exists(LOG_FILE):
            return
        if os.path.getsize(LOG_FILE) < MAX_LOG_SIZE:
            return

        # Rotate existing archives
        for i in range(MAX_LOG_ARCHIVES - 1, 0, -1):
            src = os.path.join(LOG_DIR, f"{LOG_PREFIX}_{i}.md")
            dst = os.path.join(LOG_DIR, f"{LOG_PREFIX}_{i + 1}.md")
            if os.path.exists(src):
                if i + 1 >= MAX_LOG_ARCHIVES:
                    os.remove(src)
                else:
                    os.rename(src, dst)

        # Archive current log
        archive_path = os.path.join(LOG_DIR, f"{LOG_PREFIX}_1.md")
        os.rename(LOG_FILE, archive_path)
        print(f"[LOG] Rotated log file to {archive_path}", flush=True)

        # Create new log file
        _ensure_log_file()
    except Exception as e:
        print(f"[LOG] Rotation error: {e}", flush=True)


def log_operation(operation: str, detail: str = "", status: str = "success"):
    """Log an operation to the audit trail."""
    _ensure_log_file()
    _rotate_if_needed()

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    status_icon = "✓" if status == "success" else "✗" if status == "error" else "●"

    entry = f"- {status_icon} **{timestamp}** | {operation}"
    if detail:
        entry += f" | {detail}"
    entry += "\n"

    with _lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)


def log_chat(query: str, sources_count: int):
    """Log a chat operation."""
    log_operation(
        operation="问答",
        detail=f"问题: {query[:50]}... | 来源: {sources_count}个",
        status="success"
    )


def log_index(chunks_count: int):
    """Log an indexing operation."""
    log_operation(
        operation="索引",
        detail=f"索引 {chunks_count} 个 chunks",
        status="success"
    )


def log_conflict_scan(conflicts_count: int):
    """Log a conflict scan operation."""
    log_operation(
        operation="冲突扫描",
        detail=f"发现 {conflicts_count} 个冲突",
        status="success"
    )


def log_error(operation: str, error: str):
    """Log an error."""
    log_operation(
        operation=operation,
        detail=f"错误: {error[:100]}",
        status="error"
    )


def get_recent_logs(count: int = 20) -> list:
    """Get recent log entries, including archived logs if needed."""
    _ensure_log_file()
    all_lines = []

    with _lock:
        # Read archived logs (newest first)
        for i in range(1, MAX_LOG_ARCHIVES + 1):
            archive = os.path.join(LOG_DIR, f"{LOG_PREFIX}_{i}.md")
            if os.path.exists(archive):
                with open(archive, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                log_lines = [l.strip() for l in lines if l.strip().startswith(("- ✓", "- ✗", "- ●"))]
                all_lines = log_lines + all_lines

        # Read current log
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        log_lines = [l.strip() for l in lines if l.strip().startswith(("- ✓", "- ✗", "- ●"))]
        all_lines = all_lines + log_lines

    return all_lines[-count:]
