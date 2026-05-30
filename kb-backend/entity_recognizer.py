"""
Entity recognition module for scientific terms.
Automatically identifies genes, proteins, vectors, and other entities.
"""
import os
import re
from typing import Dict, List, Set
from config import VAULT_PATH

# Common entity patterns
GENE_PATTERNS = [
    r'\b([A-Z][A-Z0-9]{1,10})\b',  # Human genes: DNMT3A, TET2
    r'\b([A-Z][a-z0-9]{1,10})\b',  # Mouse genes: Dnmt3a, Tet2
    r'\*([a-zA-Z0-9-]+)\*',  # Italic genes: *dnmt3a*
]

PROTEIN_PATTERNS = [
    r'\b(DNMT[13][AL]?)\b',
    r'\b(TET[12]?)\b',
    r'\b(KRAB)\b',
    r'\b(Cas[0-9][a-z]?)\b',
    r'\b(dCas9)\b',
    r'\b(SpCas9)\b',
]

VECTOR_PATTERNS = [
    r'\b(pLV-[A-Za-z0-9-]+)\b',
    r'\b(pAAV-[A-Za-z0-9-]+)\b',
    r'\b(pUC[0-9]{0,2})\b',
    r'\b(pET-[A-Za-z0-9-]+)\b',
]

METHOD_PATTERNS = [
    r'\b(BSP)\b',
    r'\b(WGBS)\b',
    r'\b(ChIP-seq)\b',
    r'\b(RNA-seq)\b',
    r'\b(ATAC-seq)\b',
    r'\b(qPCR)\b',
    r'\b(Western blot)\b',
    r'\b(ELISA)\b',
]

CRISPR_PATTERNS = [
    r'\b(CRISPRoff)\b',
    r'\b(CRISPRi)\b',
    r'\b(CRISPRa)\b',
    r'\b(CRISPR-Cas[0-9])\b',
    r'\b(sgRNA)\b',
    r'\b(gRNA)\b',
]

# Load existing entities from vault
_existing_entities = None


def _load_existing_entities() -> Dict[str, List[str]]:
    """Load existing entities from vault concept cards."""
    global _existing_entities
    if _existing_entities is not None:
        return _existing_entities

    _existing_entities = {
        "genes": [],
        "proteins": [],
        "vectors": [],
        "methods": [],
        "crispr": [],
    }

    concepts_dir = os.path.join(VAULT_PATH, "02_知识加工区", "概念卡片")
    if not os.path.exists(concepts_dir):
        return _existing_entities

    for fname in os.listdir(concepts_dir):
        if not fname.endswith('.md') or fname.startswith('模板'):
            continue
        name = fname.replace('.md', '')
        _existing_entities["genes"].append(name)
        _existing_entities["proteins"].append(name)

    return _existing_entities


def recognize_entities(text: str) -> Dict[str, List[str]]:
    """Recognize scientific entities in text."""
    entities = {
        "genes": [],
        "proteins": [],
        "vectors": [],
        "methods": [],
        "crispr": [],
        "unknown": [],
    }

    # Check for patterns
    for pattern in GENE_PATTERNS:
        matches = re.findall(pattern, text)
        entities["genes"].extend(matches)

    for pattern in PROTEIN_PATTERNS:
        matches = re.findall(pattern, text)
        entities["proteins"].extend(matches)

    for pattern in VECTOR_PATTERNS:
        matches = re.findall(pattern, text)
        entities["vectors"].extend(matches)

    for pattern in METHOD_PATTERNS:
        matches = re.findall(pattern, text)
        entities["methods"].extend(matches)

    for pattern in CRISPR_PATTERNS:
        matches = re.findall(pattern, text)
        entities["crispr"].extend(matches)

    # Deduplicate
    for key in entities:
        entities[key] = list(set(entities[key]))

    return entities


def find_related_notes(entity: str) -> List[Dict]:
    """Find notes related to an entity."""
    related = []
    concepts_dir = os.path.join(VAULT_PATH, "02_知识加工区", "概念卡片")

    if not os.path.exists(concepts_dir):
        return related

    entity_lower = entity.lower()

    for fname in os.listdir(concepts_dir):
        if not fname.endswith('.md') or fname.startswith('模板'):
            continue

        name = fname.replace('.md', '').lower()
        if entity_lower in name or name in entity_lower:
            filepath = os.path.join(concepts_dir, fname)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                related.append({
                    "name": fname.replace('.md', ''),
                    "path": f"02_知识加工区/概念卡片/{fname}",
                    "preview": content[:200],
                })
            except Exception as e:
                print(f"[ENTITY] Error reading {filepath}: {e}", flush=True)

    return related


def generate_links(text: str) -> List[str]:
    """Generate [[wikilinks]] for recognized entities."""
    entities = recognize_entities(text)
    links = []

    for entity in entities["genes"]:
        links.append(f"[[{entity}]]")
    for entity in entities["proteins"]:
        links.append(f"[[{entity}]]")
    for entity in entities["crispr"]:
        links.append(f"[[{entity}]]")

    return list(set(links))
