import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import VAULT_PATH
from locale import t

skip_dirs = {'.obsidian', '.update_backup', '.git', 'node_modules', 'kb-backend', 'kb-plugin'}
debounce_delay = 10

_paused = threading.Event()
_paused.set()  # Not paused by default

# Track processed files to avoid reprocessing
_processed_files = set()
_processed_lock = threading.Lock()


class VaultHandler(FileSystemEventHandler):
    def __init__(self):
        self._pending = {}
        self._lock = threading.Lock()

    def _is_relevant(self, path):
        if not path.endswith('.md'):
            return False
        parts = path.replace('\\', '/').split('/')
        for p in parts[:-1]:
            if p in skip_dirs:
                return False
        return True

    def _debounced_reindex(self, path):
        with self._lock:
            self._pending[path] = time.time()
        threading.Timer(debounce_delay, self._process_pending).start()

    def _process_pending(self):
        _paused.wait()  # Wait if paused
        with self._lock:
            now = time.time()
            to_process = {p: t for p, t in self._pending.items() if now - t >= debounce_delay}
            for p in to_process:
                del self._pending[p]
        if not to_process:
            return
        from embeddings import embed_progress
        if embed_progress.get("running"):
            print(f"[WATCHER] {t('watcher_skip')}", flush=True)
            return

        # Incremental update: only process changed files
        from vectorstore import remove_by_source, add_documents
        from indexer import index_single_file

        print(f"[WATCHER] {t('watcher_update', count=len(to_process))}", flush=True)
        for file_path in to_process:
            try:
                rel_path = os.path.relpath(file_path, VAULT_PATH).replace('\\', '/')
                # Remove old chunks for this file
                remove_by_source(rel_path)
                # Index and add new chunks
                documents = index_single_file(file_path)
                if documents:
                    add_documents(documents)
                    print(f"[WATCHER] {t('watcher_updated', path=rel_path, count=len(documents))}", flush=True)
            except Exception as e:
                print(f"[WATCHER] {t('watcher_error', path=file_path, error=e)}", flush=True)

        # Content-aware processing for new files
        for path in to_process:
            self._process_content(path)

    def _process_content(self, file_path):
        """Process file content based on type (daily notes, experiments, etc.)."""
        with _processed_lock:
            if file_path in _processed_files:
                return
            _processed_files.add(file_path)

        # Run content processing in background
        threading.Thread(
            target=self._content_process_thread,
            args=(file_path,),
            daemon=True
        ).start()

    def _content_process_thread(self, file_path):
        """Background thread for content processing."""
        try:
            import asyncio
            from content_processor import process_file_content, append_processing_result

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(process_file_content(file_path))
                if result:
                    append_processing_result(file_path, result)
                    print(f"[WATCHER] Content processed: {os.path.basename(file_path)}", flush=True)
            finally:
                loop.close()
        except Exception as e:
            print(f"[WATCHER] Content processing error for {file_path}: {e}", flush=True)

    def on_created(self, event):
        if not event.is_directory and self._is_relevant(event.src_path):
            self._debounced_reindex(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._is_relevant(event.src_path):
            self._debounced_reindex(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory and self._is_relevant(event.src_path):
            from vectorstore import remove_by_source
            rel = os.path.relpath(event.src_path, VAULT_PATH).replace('\\', '/')
            remove_by_source(rel)
            print(f"[WATCHER] {t('watcher_removed', path=rel)}", flush=True)

    def on_moved(self, event):
        if not event.is_directory:
            if self._is_relevant(event.dest_path):
                self._debounced_reindex(event.dest_path)
            # Also remove old path if it was relevant
            if self._is_relevant(event.src_path):
                from vectorstore import remove_by_source
                rel = os.path.relpath(event.src_path, VAULT_PATH).replace('\\', '/')
                remove_by_source(rel)


_observer = None


def pause_watcher():
    _paused.clear()
    print(f"[WATCHER] {t('watcher_paused')}", flush=True)


def resume_watcher():
    _paused.set()
    print(f"[WATCHER] {t('watcher_resumed')}", flush=True)


def start_watcher():
    global _observer
    if _observer and _observer.is_alive():
        return
    handler = VaultHandler()
    _observer = Observer()
    _observer.schedule(handler, VAULT_PATH, recursive=True)
    _observer.daemon = True
    _observer.start()
    print(f"[WATCHER] {t('watcher_started')}", flush=True)


def stop_watcher():
    global _observer
    if _observer and _observer.is_alive():
        _observer.stop()
        _observer.join(timeout=5)
        print(f"[WATCHER] {t('watcher_stopped')}", flush=True)
