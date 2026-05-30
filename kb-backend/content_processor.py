"""
Content-aware file processor for Obsidian vault.
Processes different file types with specialized prompts.
"""
import os
import re
import time
from typing import Optional, Dict
from config import VAULT_PATH
from llm import chat_ollama

# Processing prompts for different file types
DAILY_NOTE_PROMPT = """你是一个科研笔记整理助手。请处理以下每日笔记，提取关键信息。

原始内容：
{content}

请完成：
1. 提取所有科研相关知识点，格式：- [[知识点]]：说明
2. 提取实验想法和下一步计划
3. 提取待办事项，使用 - [ ] 格式
4. 如果提到实验问题，记录到问题与解决方案部分

输出格式：
## 知识点提取
（提取的知识点）

## 实验想法
（实验想法和计划）

## 待办事项
（待办事项）

## 问题记录
（如有实验问题，记录在这里）"""

EXPERIMENT_NOTE_PROMPT = """你是一个实验记录整理助手。请将以下实验记录整理为标准格式。

原始内容：
{content}

请整理为以下格式：
## 实验目的
（实验目的）

## 实验材料
（试剂、耗材、设备）

## 实验步骤
（关键步骤和参数）

## 实验结果
（结果描述）

## 问题分析
（如实验失败，列出可能原因和解决方案）

## 下一步计划
（后续计划）"""

LITERATURE_NOTE_PROMPT = """你是一个文献整理助手。请提取以下文献笔记的核心信息。

原始内容：
{content}

请提取：
1. 核心科学问题和创新点（3-5条）
2. 使用的 CRISPR 系统/载体/细胞系
3. 关键基因/蛋白/突变位点
4. 关键实验方法和参数
5. 重要结论
6. 对 CRISPRoff/甲基化编辑研究的启示

输出格式：
## 核心创新点
（3-5条创新点）

## 技术方法
（使用的系统、载体、细胞系）

## 关键发现
（重要结果和结论）

## 研究启示
（对我研究的启发）"""

PROBLEM_NOTE_PROMPT = """你是一个实验问题分析助手。请分析以下实验问题并提供解决方案。

问题描述：
{content}

请提供：
1. 问题分类（技术问题/试剂问题/设备问题/操作问题）
2. 可能原因（3-5个）
3. 解决方案（按优先级排列）
4. 预防措施

输出格式：
## 问题分类
（问题类型）

## 可能原因
1. （原因1）
2. （原因2）
3. （原因3）

## 解决方案
1. （方案1）
2. （方案2）
3. （方案3）

## 预防措施
（预防方法）"""


def detect_file_type(file_path: str) -> str:
    """Detect file type based on path and content."""
    rel_path = os.path.relpath(file_path, VAULT_PATH).replace("\\", "/")
    rel_path_lower = rel_path.lower()

    # Directory-based detection (new structure)
    if "01_输入区/每日笔记" in rel_path:
        return "daily_note"
    if "01_输入区/实验记录" in rel_path or "02_知识加工区/实验方法库" in rel_path:
        return "experiment"
    if "01_输入区/文献笔记" in rel_path or "01_输入区/书籍笔记" in rel_path:
        return "literature"
    if "02_知识加工区/问题与解决方案" in rel_path:
        return "problem"
    if "02_知识加工区/概念卡片" in rel_path:
        return "concept"
    if "03_输出区" in rel_path:
        return "output"

    # Content-based detection (fallback)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(500).lower()
        if any(kw in content for kw in ['实验', 'protocol', '步骤', '试剂']):
            return "experiment"
        if any(kw in content for kw in ['文献', '论文', 'abstract', '结论']):
            return "literature"
        if any(kw in content for kw in ['问题', '失败', 'error', 'troubleshoot']):
            return "problem"
    except Exception as e:
        print(f"[PROCESSOR] Content detection error for {file_path}: {e}", flush=True)

    return "unknown"


def get_prompt_for_type(file_type: str, content: str) -> Optional[str]:
    """Get the appropriate prompt for a file type."""
    prompts = {
        "daily_note": DAILY_NOTE_PROMPT,
        "experiment": EXPERIMENT_NOTE_PROMPT,
        "literature": LITERATURE_NOTE_PROMPT,
        "problem": PROBLEM_NOTE_PROMPT,
    }
    prompt_template = prompts.get(file_type)
    if prompt_template:
        return prompt_template.format(content=content[:3000])
    return None


async def process_file_content(file_path: str) -> Optional[Dict]:
    """Process a file based on its type and return structured content."""
    file_type = detect_file_type(file_path)

    if file_type in ("concept", "output", "unknown"):
        return None  # Skip these types

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[PROCESSOR] Error reading {file_path}: {e}", flush=True)
        return None

    # Skip if already processed
    if "ai_processed: true" in content[:500]:
        return None

    prompt = get_prompt_for_type(file_type, content)
    if not prompt:
        return None

    try:
        messages = [{"role": "user", "content": prompt}]
        response = await chat_ollama(messages)

        return {
            "file_path": file_path,
            "file_type": file_type,
            "processed_content": response,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        print(f"[PROCESSOR] LLM error for {file_path}: {e}", flush=True)
        return None


def append_processing_result(file_path: str, result: Dict):
    """Append processing result to the original file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add ai_processed flag to frontmatter
        if content.startswith("---"):
            # Insert ai_processed flag after first ---
            content = content.replace("---\n", "---\nai_processed: true\n", 1)
        else:
            content = f"---\nai_processed: true\n---\n{content}"

        # Append processed content
        separator = "\n\n---\n\n## AI 自动整理\n"
        content += separator + result["processed_content"]

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[PROCESSOR] Updated: {os.path.basename(file_path)}", flush=True)
    except Exception as e:
        print(f"[PROCESSOR] Error writing {file_path}: {e}", flush=True)


def update_global_index():
    """Update the global knowledge base index file."""
    index_path = os.path.join(VAULT_PATH, "00_系统", "全局知识库索引.md")

    # Count files in different directories
    stats = {
        "total": 0,
        "concepts": 0,
        "literature": 0,
        "protocols": 0,
        "scholars": 0,
        "problems": 0,
    }

    recent_files = []
    seven_days_ago = time.time() - 7 * 24 * 3600

    for root, dirs, files in os.walk(VAULT_PATH):
        # Skip system directories
        rel_root = os.path.relpath(root, VAULT_PATH)
        if any(skip in rel_root for skip in [".obsidian", "kb-backend", "kb-plugin", ".git", "node_modules"]):
            continue

        for fname in files:
            if not fname.endswith('.md'):
                continue

            stats["total"] += 1
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, VAULT_PATH).replace("\\", "/")

            # Count by directory (new structure)
            if rel_path.startswith("02_知识加工区/概念卡片/"):
                stats["concepts"] += 1
            elif rel_path.startswith("01_输入区/文献笔记/"):
                stats["literature"] += 1
            elif rel_path.startswith("02_知识加工区/实验方法库/"):
                stats["protocols"] += 1
            elif rel_path.startswith("02_知识加工区/学者信息/"):
                stats["scholars"] += 1
            elif rel_path.startswith("02_知识加工区/问题与解决方案/"):
                stats["problems"] += 1

            # Track recent files
            try:
                mtime = os.path.getmtime(fpath)
                if mtime > seven_days_ago:
                    recent_files.append((mtime, rel_path, fname.replace('.md', '')))
            except Exception as e:
                print(f"[INDEX] Error reading {fpath}: {e}", flush=True)

    # Sort recent files by modification time
    recent_files.sort(reverse=True)
    recent_files = recent_files[:20]

    # Generate index content
    recent_section = ""
    for mtime, rel_path, title in recent_files:
        date_str = time.strftime("%Y-%m-%d", time.localtime(mtime))
        recent_section += f"- [[{rel_path}|{title}]] ({date_str})\n"

    if not recent_section:
        recent_section = "（暂无最近更新）\n"

    index_content = f"""# 全局知识库索引

> 此文件由知识库助手自动维护，最后更新：{time.strftime("%Y-%m-%d %H:%M:%S")}

## 知识库统计

- 总文件数：{stats['total']}
- 概念卡片：{stats['concepts']}
- 文献笔记：{stats['literature']}
- 实验方法：{stats['protocols']}
- 学者信息：{stats['scholars']}
- 问题案例：{stats['problems']}

## 最近 7 天更新

{recent_section}
## 分类索引

### 输入区（01_输入区）
- [[01_输入区/每日笔记/|每日笔记]]
- [[01_输入区/文献笔记/|文献笔记]]
- [[01_输入区/书籍笔记/|书籍笔记]]
- [[01_输入区/实验记录/|实验记录]]

### 知识加工区（02_知识加工区）
- [[02_知识加工区/基因实体库/|基因实体库]]
- [[02_知识加工区/蛋白与结构域/|蛋白与结构域]]
- [[02_知识加工区/载体与质粒/|载体与质粒]]
- [[02_知识加工区/sgRNA数据库/|sgRNA数据库]]
- [[02_知识加工区/实验方法库/|实验方法库]]
- [[02_知识加工区/概念卡片/|概念卡片]]
- [[02_知识加工区/试剂配制/|试剂配制]]
- [[02_知识加工区/学者信息/|学者信息]]
- [[02_知识加工区/文献综述/|文献综述]]
- [[02_知识加工区/实验结果分析/|实验结果分析]]
- [[02_知识加工区/问题与解决方案/|问题与解决方案]]

### 输出区（03_输出区）
- [[03_输出区/论文草稿/|论文草稿]]
- [[03_输出区/项目文档/|项目文档]]

### 系统配置（00_系统）
- [[00_系统/全局知识库索引.md|全局知识库索引]]
- [[00_系统/专业术语规范.md|专业术语规范]]
"""

    try:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"[INDEX] Global index updated", flush=True)
    except Exception as e:
        print(f"[INDEX] Error updating index: {e}", flush=True)
