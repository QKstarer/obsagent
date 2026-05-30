"""
Paper writing assistant.
Auto-generates methods and results sections based on experiment records.
"""
import os
import time
from typing import Dict, List, Optional
from config import VAULT_PATH
from llm import chat_ollama
from vectorstore import collection

WRITING_DIR = os.path.join(VAULT_PATH, "03_输出区", "论文草稿")
os.makedirs(WRITING_DIR, exist_ok=True)

METHODS_PROMPT = """根据以下实验记录，生成论文的"材料与方法"部分。

实验记录：
{experiment_records}

相关试剂和载体：
{reagents}

请生成标准的"材料与方法"部分，包含：
1. 细胞培养方法
2. 载体构建和 sgRNA 设计
3. 转染/递送方法
4. 甲基化分析方法（BSP/WGBS）
5. 数据分析方法

使用学术论文的写作风格，简洁准确。"""

RESULTS_PROMPT = """根据以下实验结果，生成论文的"结果"部分。

实验结果：
{experiment_results}

请生成标准的"结果"部分，包含：
1. 实验目的（1句话）
2. 实验方法（简述）
3. 实验结果（描述观察到的现象）
4. 结果解读（1-2句话）

使用学术论文的写作风格，客观描述。"""

DISCUSSION_PROMPT = """根据以下研究内容，生成论文的"讨论"部分框架。

研究主题：{topic}
核心发现：{findings}
相关文献：{literature}

请生成"讨论"部分框架，包含：
1. 研究总结（2-3句话）
2. 与已有研究的比较
3. 研究意义
4. 局限性
5. 未来方向

使用学术论文的写作风格。"""


def scan_experiment_records(gene: Optional[str] = None, days: int = 30) -> List[Dict]:
    """Scan vault for recent experiment records."""
    cutoff_time = time.time() - days * 24 * 3600
    records = []

    for root, dirs, files in os.walk(VAULT_PATH):
        rel_root = os.path.relpath(root, VAULT_PATH)
        if any(skip in rel_root for skip in [".obsidian", ".git", "kb-backend", "kb-plugin"]):
            continue

        for fname in files:
            if not fname.endswith('.md'):
                continue

            fpath = os.path.join(root, fname)
            try:
                mtime = os.path.getmtime(fpath)
                if mtime < cutoff_time:
                    continue

                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read(1000)

                # Check if it's an experiment record
                is_experiment = any([
                    "实验" in fname,
                    "experiment" in fname.lower(),
                    "实验记录" in rel_root,
                    "实验结果" in rel_root,
                    "转染" in content[:500],
                    "BSP" in content[:500],
                ])

                if not is_experiment:
                    continue

                # Filter by gene if specified
                if gene and gene.lower() not in content.lower():
                    continue

                records.append({
                    "path": os.path.relpath(fpath, VAULT_PATH).replace("\\", "/"),
                    "name": fname.replace('.md', ''),
                    "mtime": mtime,
                    "preview": content[:500],
                })
            except Exception as e:
                print(f"[WRITING] Error reading {fpath}: {e}", flush=True)

    return records


async def generate_methods_section(gene: str) -> str:
    """Generate methods section based on experiment records."""
    records = scan_experiment_records(gene)

    if not records:
        return "未找到相关实验记录。请先在 01_输入区/实验记录 中添加实验记录。"

    # Build experiment records text
    experiment_text = ""
    for r in records[:10]:
        experiment_text += f"\n【{r['name']}】\n{r['preview']}\n"

    # Get reagent information from knowledge base
    try:
        all_docs = collection.get(include=["metadatas", "documents"])
        reagents = ""
        for i, meta in enumerate(all_docs["metadatas"]):
            if "试剂" in meta.get("source", "") or "载体" in meta.get("source", ""):
                if gene.lower() in all_docs["documents"][i].lower():
                    reagents += f"- {meta.get('title', '')}\n"
    except Exception as e:
        print(f"[WRITING] Error fetching reagents: {e}", flush=True)
        reagents = "（无法获取试剂信息）"

    prompt = METHODS_PROMPT.format(
        experiment_records=experiment_text,
        reagents=reagents,
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        return await chat_ollama(messages)
    except Exception as e:
        return f"生成失败：{e}"


async def generate_results_section(experiment_name: str) -> str:
    """Generate results section for a specific experiment."""
    # Find the experiment record
    records = scan_experiment_records()
    target_record = None

    for r in records:
        if experiment_name.lower() in r["name"].lower():
            target_record = r
            break

    if not target_record:
        return f"未找到实验记录：{experiment_name}"

    # Read full content
    fpath = os.path.join(VAULT_PATH, target_record["path"])
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read(3000)
    except Exception as e:
        print(f"[WRITING] Error reading experiment record: {e}", flush=True)
        return "无法读取实验记录。"

    prompt = RESULTS_PROMPT.format(experiment_results=content)

    try:
        messages = [{"role": "user", "content": prompt}]
        return await chat_ollama(messages)
    except Exception as e:
        return f"生成失败：{e}"


async def generate_discussion_section(topic: str) -> str:
    """Generate discussion section framework."""
    # Search for related content
    try:
        all_docs = collection.get(include=["metadatas", "documents"])
        related = []
        for i, meta in enumerate(all_docs["metadatas"]):
            if topic.lower() in all_docs["documents"][i].lower():
                related.append({
                    "title": meta.get("title", ""),
                    "source": meta.get("source", ""),
                    "preview": all_docs["documents"][i][:300],
                })
        related = related[:10]
    except Exception as e:
        print(f"[WRITING] Error searching related content: {e}", flush=True)
        related = []

    # Build literature text
    literature = ""
    for r in related:
        literature += f"- {r['title']} ({r['source']})\n"

    prompt = DISCUSSION_PROMPT.format(
        topic=topic,
        findings="（请在对话中提供核心发现）",
        literature=literature,
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        return await chat_ollama(messages)
    except Exception as e:
        return f"生成失败：{e}"


def save_writing(content: str, section_type: str, topic: str) -> str:
    """Save generated writing to the vault."""
    date_str = time.strftime("%Y-%m-%d")
    filename = f"{date_str}_{topic}_{section_type}.md"
    filepath = os.path.join(WRITING_DIR, filename)

    full_content = f"""---
ai_generated: true
date: {date_str}
tags:
  - 论文写作
  - {section_type}
  - {topic}
type: writing
---

# {topic} - {section_type}

> 生成日期：{date_str}
> 由知识库助手自动生成，请根据实际情况修改

{content}

---
*此内容由知识库助手自动生成，请仔细校对和修改*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"[WRITING] Saved: {filename}", flush=True)
    return filepath


def get_writing_stats() -> Dict:
    """Get writing statistics."""
    if not os.path.exists(WRITING_DIR):
        return {"total": 0, "sections": {}}

    files = [f for f in os.listdir(WRITING_DIR) if f.endswith(".md")]
    sections = {}
    for f in files:
        if "材料" in f or "方法" in f:
            sections["材料与方法"] = sections.get("材料与方法", 0) + 1
        elif "结果" in f:
            sections["结果"] = sections.get("结果", 0) + 1
        elif "讨论" in f:
            sections["讨论"] = sections.get("讨论", 0) + 1
        else:
            sections["其他"] = sections.get("其他", 0) + 1

    return {
        "total": len(files),
        "sections": sections,
    }
