"""
Experiment failure case tracker.
Automatically extracts failure cases from Q&A and stores them in the knowledge base.
"""
import os
import re
import time
from typing import Optional, Dict, List
from config import VAULT_PATH
from llm import chat_ollama

FAILURE_DIR = os.path.join(VAULT_PATH, "02_知识加工区", "问题与解决方案")
os.makedirs(FAILURE_DIR, exist_ok=True)

FAILURE_DETECT_PROMPT = """判断以下对话是否涉及实验问题或失败案例。

问题：{query}
回答：{answer}

如果涉及实验问题/失败/故障排查，返回 JSON：
{{"is_failure": true, "problem": "问题简述", "category": "技术问题/试剂问题/设备问题/操作问题/数据分析"}}

如果不涉及，返回：
{{"is_failure": false}}"""

FAILURE_EXTRACT_PROMPT = """从以下对话中提取实验失败案例的结构化信息。

问题：{query}
回答：{answer}

请提取并返回 JSON 格式：
{{
  "problem": "问题简述",
  "category": "技术问题/试剂问题/设备问题/操作问题/数据分析",
  "symptoms": ["症状1", "症状2"],
  "possible_causes": ["原因1", "原因2", "原因3"],
  "solutions": ["方案1", "方案2", "方案3"],
  "prevention": ["预防措施1", "预防措施2"],
  "related_concepts": ["相关概念1", "相关概念2"]
}}"""


async def detect_failure_case(query: str, answer: str) -> Optional[Dict]:
    """Detect if a Q&A involves an experiment failure case."""
    prompt = FAILURE_DETECT_PROMPT.format(query=query, answer=answer[:1000])
    try:
        messages = [{"role": "user", "content": prompt}]
        response = await chat_ollama(messages)
        response = response.strip()
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            import json
            result = json.loads(response[start:end])
            if result.get("is_failure"):
                return result
    except Exception as e:
        print(f"[FAILURE] Detection error: {e}", flush=True)
    return None


async def extract_failure_case(query: str, answer: str) -> Optional[Dict]:
    """Extract structured failure case information."""
    prompt = FAILURE_EXTRACT_PROMPT.format(query=query, answer=answer[:2000])
    try:
        messages = [{"role": "user", "content": prompt}]
        response = await chat_ollama(messages)
        response = response.strip()
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            import json
            result = json.loads(response[start:end])
            return result
    except Exception as e:
        print(f"[FAILURE] Extraction error: {e}", flush=True)
    return None


def save_failure_case(case_data: Dict, query: str) -> str:
    """Save a failure case to the knowledge base."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    date_str = time.strftime("%Y-%m-%d")

    problem = case_data.get("problem", "未知问题")
    category = case_data.get("category", "未分类")
    symptoms = case_data.get("symptoms", [])
    causes = case_data.get("possible_causes", [])
    solutions = case_data.get("solutions", [])
    prevention = case_data.get("prevention", [])
    related = case_data.get("related_concepts", [])

    # Generate filename
    safe_problem = problem[:30].replace("/", "_").replace("\\", "_").replace(":", "_")
    safe_problem = "".join(c for c in safe_problem if c.isalnum() or c in " _-" or '一' <= c <= '鿿')
    safe_problem = safe_problem.strip() or "问题"
    filename = f"{date_str}_{safe_problem}.md"
    filepath = os.path.join(FAILURE_DIR, filename)

    # Build symptoms list
    symptoms_text = "\n".join([f"- {s}" for s in symptoms]) if symptoms else "- （待补充）"

    # Build causes list
    causes_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(causes)]) if causes else "1. （待分析）"

    # Build solutions list
    solutions_text = "\n".join([f"### 方案 {i+1}\n- {s}" for i, s in enumerate(solutions)]) if solutions else "### 方案 1\n- （待补充）"

    # Build prevention list
    prevention_text = "\n".join([f"- {p}" for p in prevention]) if prevention else "- （待补充）"

    # Build related concepts
    related_text = "\n".join([f"- [[{c}]]" for c in related]) if related else "- （待关联）"

    content = f"""---
ai_processed: true
date: {date_str}
tags:
  - troubleshooting
  - {category}
  - 实验失败
type: problem
---

# {problem}

> 记录时间：{timestamp}
> 问题分类：{category}

## 问题描述

{query}

## 问题症状

{symptoms_text}

## 可能原因

{causes_text}

## 解决方案

{solutions_text}

## 预防措施

{prevention_text}

## 相关概念

{related_text}

## 原始问答

> **问题**：{query}

> **回答**：{answer[:500]}...

---
*此案例由知识库助手自动提取*
"""

    # Check if similar problem already exists
    existing_files = [f for f in os.listdir(FAILURE_DIR) if f.endswith(".md") and not f.startswith("模板")]
    for ef in existing_files:
        if safe_problem[:15] in ef:
            # Append to existing file
            filepath = os.path.join(FAILURE_DIR, ef)
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n## 补充记录 ({date_str})\n\n")
                f.write(f"**问题**：{query}\n\n")
                f.write(f"**可能原因**：\n{causes_text}\n\n")
                f.write(f"**解决方案**：\n{solutions_text}\n")
            print(f"[FAILURE] Appended to existing: {ef}", flush=True)
            return filepath

    # Create new file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[FAILURE] Created: {filename}", flush=True)
    return filepath


async def process_failure_from_chat(query: str, answer: str):
    """Process a chat response to detect and save failure cases."""
    # First detect if it's a failure case
    detection = await detect_failure_case(query, answer)
    if not detection:
        return

    print(f"[FAILURE] Detected failure case: {detection.get('problem', 'unknown')}", flush=True)

    # Extract structured information
    case_data = await extract_failure_case(query, answer)
    if not case_data:
        # Use detection data as fallback
        case_data = {
            "problem": detection.get("problem", query[:50]),
            "category": detection.get("category", "未分类"),
            "symptoms": [],
            "possible_causes": [],
            "solutions": [],
            "prevention": [],
            "related_concepts": [],
        }

    # Save to knowledge base
    save_failure_case(case_data, query)


def get_failure_stats() -> Dict:
    """Get failure case statistics."""
    if not os.path.exists(FAILURE_DIR):
        return {"total": 0, "categories": {}}

    files = [f for f in os.listdir(FAILURE_DIR) if f.endswith(".md") and not f.startswith("模板")]
    categories = {}
    for f in files:
        # Try to extract category from filename
        if "技术" in f:
            categories["技术问题"] = categories.get("技术问题", 0) + 1
        elif "试剂" in f:
            categories["试剂问题"] = categories.get("试剂问题", 0) + 1
        elif "设备" in f:
            categories["设备问题"] = categories.get("设备问题", 0) + 1
        else:
            categories["其他"] = categories.get("其他", 0) + 1

    return {
        "total": len(files),
        "categories": categories,
    }
