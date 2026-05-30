"""
Auto-linking module for Obsidian vault.
Automatically adds [[wikilinks]] to notes based on entity recognition.
"""
import os
import re
from typing import Dict, List
from config import VAULT_PATH
from entity_recognizer import recognize_entities, _load_existing_entities


def scan_vault_for_entities() -> Dict[str, List[str]]:
    """Scan vault and collect all entity names."""
    entities = {
        "genes": set(),
        "proteins": set(),
        "vectors": set(),
        "methods": set(),
        "crispr": set(),
    }

    # Scan concept cards
    concepts_dir = os.path.join(VAULT_PATH, "02_知识加工区", "概念卡片")
    if os.path.exists(concepts_dir):
        for fname in os.listdir(concepts_dir):
            if fname.endswith('.md') and not fname.startswith('模板'):
                name = fname.replace('.md', '')
                entities["genes"].add(name)
                entities["proteins"].add(name)

    # Scan sgRNA database
    sgrna_dir = os.path.join(VAULT_PATH, "02_知识加工区", "sgRNA数据库")
    if os.path.exists(sgrna_dir):
        for fname in os.listdir(sgrna_dir):
            if fname.endswith('.md') and not fname.startswith('模板'):
                name = fname.replace('.md', '')
                entities["genes"].add(name)

    # Scan vectors
    vector_dir = os.path.join(VAULT_PATH, "02_知识加工区", "载体与质粒")
    if os.path.exists(vector_dir):
        for root, dirs, files in os.walk(vector_dir):
            for fname in files:
                if fname.endswith('.md') and not fname.startswith('模板'):
                    name = fname.replace('.md', '')
                    entities["vectors"].add(name)

    return {k: list(v) for k, v in entities.items()}


def add_links_to_text(text: str, entities: Dict[str, List[str]]) -> str:
    """Add [[wikilinks]] to text based on entity names."""
    # Build a mapping of entity names to their linked versions
    link_map = {}

    for entity in entities.get("genes", []):
        if len(entity) >= 2:  # Skip very short names
            link_map[entity] = f"[[{entity}]]"

    for entity in entities.get("proteins", []):
        if len(entity) >= 2:
            link_map[entity] = f"[[{entity}]]"

    for entity in entities.get("vectors", []):
        if len(entity) >= 2:
            link_map[entity] = f"[[{entity}]]"

    for entity in entities.get("crispr", []):
        if len(entity) >= 2:
            link_map[entity] = f"[[{entity}]]"

    # Sort by length (longest first) to avoid partial matches
    sorted_entities = sorted(link_map.keys(), key=len, reverse=True)

    # Replace entity names with links
    result = text
    for entity in sorted_entities:
        # Only replace if not already inside [[ ]]
        pattern = r'(?<!\[\[)(' + re.escape(entity) + r')(?!\]\])'
        result = re.sub(pattern, link_map[entity], result)

    return result


def process_file_links(filepath: str) -> Dict:
    """Process a file and add links to entities."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get all entities from vault
        entities = scan_vault_for_entities()

        # Add links to content
        linked_content = add_links_to_text(content, entities)

        # Count new links added
        original_links = len(re.findall(r'\[\[.*?\]\]', content))
        new_links = len(re.findall(r'\[\[.*?\]\]', linked_content))
        links_added = new_links - original_links

        if links_added > 0:
            # Write back to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(linked_content)

            return {
                "success": True,
                "links_added": links_added,
                "total_links": new_links,
            }

        return {
            "success": True,
            "links_added": 0,
            "total_links": original_links,
        }

    except Exception as e:
        return {"error": f"Failed to process file: {e}"}


def batch_process_links(directory: str) -> List[Dict]:
    """Process all files in a directory and add links."""
    results = []

    for root, dirs, files in os.walk(directory):
        # Skip system directories
        if any(skip in root for skip in [".obsidian", "kb-backend", "kb-plugin", ".git"]):
            continue

        for fname in files:
            if not fname.endswith('.md'):
                continue

            filepath = os.path.join(root, fname)
            result = process_file_links(filepath)
            result["file"] = os.path.relpath(filepath, VAULT_PATH)
            results.append(result)

    return results
