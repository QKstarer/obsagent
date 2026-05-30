import os
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from config import VAULT_PATH, CHUNK_SIZE, CHUNK_OVERLAP


def parse_frontmatter(content: str) -> tuple:
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            meta = {}
        body = content[match.end():]
        return meta, body
    return {}, content


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    paragraphs = re.split(r'\n{2,}', text)
    chunks = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) < chunk_size:
            current += "\n\n" + para if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > chunk_size:
                words = para.split()
                sub = ""
                for w in words:
                    if len(sub) + len(w) < chunk_size:
                        sub += " " + w if sub else w
                    else:
                        if sub:
                            chunks.append(sub)
                        sub = w
                if sub:
                    current = sub
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks


def index_vault(vault_path: str = VAULT_PATH) -> List[Dict]:
    documents = []
    skip_dirs = {'.obsidian', '.update_backup', '.git', 'node_modules', 'kb-backend', 'kb-plugin'}
    skip_files = {'longform-sessions.json', 'manifest.json', 'README.md'}

    for root, dirs, files in os.walk(vault_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        rel_root = os.path.relpath(root, vault_path)
        if rel_root.startswith('.'):
            continue

        for fname in files:
            if not fname.endswith('.md') or fname in skip_files:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                continue

            meta, body = parse_frontmatter(content)
            if not body.strip():
                continue

            title = meta.get('name', fname.replace('.md', ''))
            tags = meta.get('tags', []) or []
            aliases = meta.get('aliases', []) or []
            if isinstance(tags, str):
                tags = [tags]
            if isinstance(aliases, str):
                aliases = [aliases]
            tags = [t for t in tags if isinstance(t, str)]
            aliases = [a for a in aliases if isinstance(a, str)]
            rel_path = os.path.relpath(fpath, vault_path).replace('\\', '/')

            chunks = chunk_text(body)
            for i, chunk in enumerate(chunks):
                documents.append({
                    'id': f"{rel_path}::chunk_{i}",
                    'text': chunk,
                    'metadata': {
                        'source': rel_path,
                        'title': title,
                        'tags': ', '.join(tags) if isinstance(tags, list) else str(tags),
                        'aliases': ', '.join(aliases) if isinstance(aliases, list) else str(aliases),
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                    }
                })

    print(f"[INDEXER] Indexed {len(documents)} chunks from {len(set(d['metadata']['source'] for d in documents))} files")
    return documents


def index_single_file(file_path: str, vault_path: str = VAULT_PATH) -> List[Dict]:
    """Index a single file and return its chunks."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[INDEXER] Error reading {file_path}: {e}", flush=True)
        return []

    meta, body = parse_frontmatter(content)
    if not body.strip():
        return []

    title = meta.get('name', os.path.basename(file_path).replace('.md', ''))
    tags = meta.get('tags', []) or []
    aliases = meta.get('aliases', []) or []
    if isinstance(tags, str):
        tags = [tags]
    if isinstance(aliases, str):
        aliases = [aliases]
    tags = [t for t in tags if isinstance(t, str)]
    aliases = [a for a in aliases if isinstance(a, str)]
    rel_path = os.path.relpath(file_path, vault_path).replace('\\', '/')

    chunks = chunk_text(body)
    documents = []
    for i, chunk in enumerate(chunks):
        documents.append({
            'id': f"{rel_path}::chunk_{i}",
            'text': chunk,
            'metadata': {
                'source': rel_path,
                'title': title,
                'tags': ', '.join(tags) if isinstance(tags, list) else str(tags),
                'aliases': ', '.join(aliases) if isinstance(aliases, list) else str(aliases),
                'chunk_index': i,
                'total_chunks': len(chunks),
            }
        })

    return documents
