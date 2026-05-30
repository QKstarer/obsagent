"""
sgRNA management system.
Manages sgRNA records, links to genes, and tracks usage.
"""
import os
import re
import time
from typing import Dict, List, Optional
from config import VAULT_PATH
from vectorstore import collection

SGRNA_DIR = os.path.join(VAULT_PATH, "02_知识加工区", "sgRNA数据库")
os.makedirs(SGRNA_DIR, exist_ok=True)

SGRNA_TEMPLATE = """---
name: {gene}_sgRNA_{number}
aliases:
  - {sequence}
tags:
  - sgRNA
  - {gene}
  - {system}
type: sgrna
---

# {gene} sgRNA {number}

## 基本信息

- **靶基因**：[[{gene}]]
- **sgRNA 序列**：5'-{sequence}-3'
- **PAM 序列**：{pam}
- **靶向区域**：{region}

## 设计参数

- **CpG 密度**：{cpg_density} 个/100bp
- **GC 含量**：{gc_content}%
- **脱靶评分**：{off_target_score}
- **设计工具**：{design_tool}

## 使用记录

| 日期 | 实验 | 载体 | 细胞系 | 效果 |
|------|------|------|--------|------|
| {date} | {experiment} | {vector} | {cell_line} | {efficiency} |

## 相关概念

- [[{gene}]]
- [[sgRNA设计规则]]
- [[CRISPRoff]]

---
*此记录由知识库助手管理*
"""


def parse_sgrna_filename(filename: str) -> Optional[Dict]:
    """Parse sgRNA filename to extract gene and number."""
    # Expected format: Gene_sgRNA_01.md
    match = re.match(r'^(.+?)_sgRNA_(\d+)\.md$', filename)
    if match:
        return {
            "gene": match.group(1),
            "number": match.group(2),
            "filename": filename,
        }
    return None


def list_sgrnas(gene: Optional[str] = None) -> List[Dict]:
    """List all sgRNA records, optionally filtered by gene."""
    if not os.path.exists(SGRNA_DIR):
        return []

    sgrnas = []
    for fname in os.listdir(SGRNA_DIR):
        if not fname.endswith('.md') or fname.startswith('模板'):
            continue

        info = parse_sgrna_filename(fname)
        if not info:
            continue

        if gene and info["gene"].lower() != gene.lower():
            continue

        filepath = os.path.join(SGRNA_DIR, fname)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read(500)

            # Extract sequence from content
            seq_match = re.search(r"5'-(.+?)-3'", content)
            sequence = seq_match.group(1) if seq_match else ""

            sgrnas.append({
                **info,
                "path": filepath,
                "sequence": sequence,
            })
        except Exception as e:
            print(f"[SGRNA] Error reading {filepath}: {e}", flush=True)
            sgrnas.append({**info, "path": filepath, "sequence": ""})

    return sgrnas


def create_sgrna_record(gene: str, sequence: str, **kwargs) -> str:
    """Create a new sgRNA record."""
    # Determine next number
    existing = list_sgrnas(gene)
    numbers = [int(s["number"]) for s in existing if s["number"].isdigit()]
    next_num = max(numbers, default=0) + 1

    # Fill template
    content = SGRNA_TEMPLATE.format(
        gene=gene,
        number=f"{next_num:02d}",
        sequence=sequence,
        pam=kwargs.get("pam", "NGG"),
        region=kwargs.get("region", "TSS 上游 bp"),
        cpg_density=kwargs.get("cpg_density", ""),
        gc_content=kwargs.get("gc_content", ""),
        off_target_score=kwargs.get("off_target_score", ""),
        design_tool=kwargs.get("design_tool", "CRISPOR"),
        date=time.strftime("%Y-%m-%d"),
        experiment=kwargs.get("experiment", ""),
        vector=kwargs.get("vector", ""),
        cell_line=kwargs.get("cell_line", ""),
        efficiency=kwargs.get("efficiency", ""),
        system=kwargs.get("system", "CRISPRoff"),
    )

    # Save file
    filename = f"{gene}_sgRNA_{next_num:02d}.md"
    filepath = os.path.join(SGRNA_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[SGRNA] Created: {filename}", flush=True)
    return filepath


def get_sgrna_stats() -> Dict:
    """Get sgRNA statistics."""
    sgrnas = list_sgrnas()

    genes = {}
    for s in sgrnas:
        gene = s["gene"]
        if gene not in genes:
            genes[gene] = 0
        genes[gene] += 1

    return {
        "total": len(sgrnas),
        "genes": genes,
        "latest": [s["filename"] for s in sgrnas[:5]],
    }


def search_sgrnas(query: str) -> List[Dict]:
    """Search sgRNA records by gene name or sequence."""
    query_lower = query.lower()
    all_sgrnas = list_sgrnas()

    results = []
    for s in all_sgrnas:
        if (query_lower in s["gene"].lower() or
            query_lower in s.get("sequence", "").lower()):
            results.append(s)

    return results
