"""
Weekly progress tracker for research projects.
Scans vault for recent changes and generates progress reports.
"""
import os
import time
from typing import Dict, List
from config import VAULT_PATH
from llm import chat_ollama

PROGRESS_DIR = os.path.join(VAULT_PATH, "03_输出区", "组会汇报")
os.makedirs(PROGRESS_DIR, exist_ok=True)

PROGRESS_PROMPT = """根据以下本周知识库更新记录，生成一份简洁的课题进度报告。

本周新增/修改的文件：
{file_list}

请生成进度报告，包含：
1. 本周工作概述（2-3句话）
2. 主要进展（3-5条）
3. 遇到的问题（如有）
4. 下周计划建议（2-3条）

使用中文，简洁明了。"""


def scan_recent_files(days: int = 7) -> List[Dict]:
    """Scan vault for files modified in the last N days."""
    cutoff_time = time.time() - days * 24 * 3600
    recent_files = []

    skip_dirs = {'.obsidian', '.git', 'node_modules', '.update_backup', '.stfolder', '.pandoc'}

    for root, dirs, files in os.walk(VAULT_PATH):
        # Skip system directories
        rel_root = os.path.relpath(root, VAULT_PATH)
        if any(skip in rel_root for skip in skip_dirs):
            continue

        for fname in files:
            if not fname.endswith('.md'):
                continue

            fpath = os.path.join(root, fname)
            try:
                mtime = os.path.getmtime(fpath)
                if mtime > cutoff_time:
                    rel_path = os.path.relpath(fpath, VAULT_PATH).replace("\\", "/")
                    recent_files.append({
                        "path": rel_path,
                        "name": fname.replace('.md', ''),
                        "mtime": mtime,
                        "date": time.strftime("%Y-%m-%d", time.localtime(mtime)),
                    })
            except Exception as e:
                print(f"[PROGRESS] Error reading {fpath}: {e}", flush=True)

    # Sort by modification time (newest first)
    recent_files.sort(key=lambda x: x["mtime"], reverse=True)
    return recent_files


def categorize_files(files: List[Dict]) -> Dict[str, List[str]]:
    """Categorize files by their directory."""
    categories = {}
    for f in files:
        path = f["path"]
        if "01_输入区/每日笔记" in path:
            cat = "每日笔记"
        elif "01_输入区/实验记录" in path:
            cat = "实验记录"
        elif "01_输入区/文献笔记" in path:
            cat = "文献笔记"
        elif "01_输入区/对话记录" in path:
            cat = "对话记录"
        elif "02_知识加工区/概念卡片" in path:
            cat = "概念卡片"
        elif "02_知识加工区/实验方法库" in path:
            cat = "实验方法"
        elif "02_知识加工区/问题与解决方案" in path:
            cat = "问题案例"
        elif "03_输出区" in path:
            cat = "输出成果"
        else:
            cat = "其他"

        if cat not in categories:
            categories[cat] = []
        categories[cat].append(f["name"])

    return categories


async def generate_progress_report(days: int = 7) -> str:
    """Generate a progress report for the last N days."""
    files = scan_recent_files(days)

    if not files:
        return "本周暂无更新记录。"

    # Categorize files
    categories = categorize_files(files)

    # Build file list for prompt
    file_list = ""
    for cat, names in categories.items():
        file_list += f"\n【{cat}】({len(names)}个)\n"
        for name in names[:10]:  # Limit to 10 per category
            file_list += f"- {name}\n"
        if len(names) > 10:
            file_list += f"- ...还有 {len(names) - 10} 个\n"

    # Generate report using LLM
    prompt = PROGRESS_PROMPT.format(file_list=file_list)
    try:
        messages = [{"role": "user", "content": prompt}]
        report_content = await chat_ollama(messages)
    except Exception as e:
        print(f"[PROGRESS] LLM error: {e}", flush=True)
        report_content = f"本周共更新 {len(files)} 个文件。\n\n"
        for cat, names in categories.items():
            report_content += f"- {cat}: {len(names)} 个\n"

    return report_content


def save_progress_report(report_content: str, days: int = 7) -> str:
    """Save progress report to the vault."""
    date_str = time.strftime("%Y-%m-%d")
    filename = f"{date_str}_周进度报告.md"
    filepath = os.path.join(PROGRESS_DIR, filename)

    files = scan_recent_files(days)
    categories = categorize_files(files)

    # Build statistics
    stats_text = ""
    for cat, names in categories.items():
        stats_text += f"- {cat}: {len(names)} 个\n"

    content = f"""---
ai_processed: true
date: {date_str}
tags:
  - 课题进展
  - 周报
type: progress
---

# 周进度报告

> 报告日期：{date_str}
> 统计周期：最近 {days} 天

## 统计概览

本周共更新 **{len(files)}** 个文件：

{stats_text}
## 进度报告

{report_content}

---
*此报告由知识库助手自动生成*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[PROGRESS] Report saved: {filename}", flush=True)
    return filepath


async def generate_weekly_report():
    """Main entry point for weekly report generation."""
    report_content = await generate_progress_report(7)
    return save_progress_report(report_content, 7)


def get_progress_stats() -> Dict:
    """Get progress statistics."""
    files = scan_recent_files(7)
    categories = categorize_files(files)

    return {
        "total_updates": len(files),
        "categories": {cat: len(names) for cat, names in categories.items()},
        "latest_files": [f["name"] for f in files[:5]],
    }
