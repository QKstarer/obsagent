"""
Output workshop module for generating structured documents.
Provides templates and quality assessment for different output types.
"""
import os
import time
from typing import Dict, List, Optional
from config import VAULT_PATH
from llm import chat_ollama

# Output templates
OUTPUT_TEMPLATES = {
    "paper": {
        "name": "论文草稿",
        "folder": "03_输出区/论文草稿",
        "tags": ["论文", "草稿"],
        "sections": ["标题", "摘要", "引言", "方法", "结果", "讨论", "结论"],
    },
    "report": {
        "name": "实验报告",
        "folder": "03_输出区/论文草稿",
        "tags": ["实验报告"],
        "sections": ["目的", "方法", "结果", "分析", "结论"],
    },
    "presentation": {
        "name": "组会汇报",
        "folder": "03_输出区/组会汇报",
        "tags": ["组会汇报"],
        "sections": ["背景", "进展", "问题", "计划"],
    },
    "protocol": {
        "name": "实验方案",
        "folder": "02_知识加工区/实验方法库",
        "tags": ["实验方案"],
        "sections": ["目的", "原理", "材料", "步骤", "注意事项"],
    },
    "review": {
        "name": "文献综述",
        "folder": "02_知识加工区/文献综述",
        "tags": ["文献综述"],
        "sections": ["摘要", "创新点", "方法", "结论", "启示"],
    },
}

# Quality assessment prompts
QUALITY_PROMPTS = {
    "paper": """请评估以下论文草稿的质量，返回JSON格式：
{
  "score": 0-100,
  "completeness": "完整/部分/缺失",
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}

论文内容：
{content}""",

    "report": """请评估以下实验报告的质量，返回JSON格式：
{
  "score": 0-100,
  "completeness": "完整/部分/缺失",
  "issues": ["问题1", "问题2"],
  "suggestions": ["建议1", "建议2"]
}

实验报告内容：
{content}""",
}


def get_output_templates() -> Dict:
    """Get all available output templates."""
    return OUTPUT_TEMPLATES


def get_template(template_type: str) -> Optional[Dict]:
    """Get a specific template."""
    return OUTPUT_TEMPLATES.get(template_type)


def create_output_document(template_type: str, title: str, content: str = "") -> str:
    """Create an output document based on template."""
    template = OUTPUT_TEMPLATES.get(template_type)
    if not template:
        return f"Unknown template type: {template_type}"

    date_str = time.strftime("%Y-%m-%d")
    folder = os.path.join(VAULT_PATH, template["folder"])
    os.makedirs(folder, exist_ok=True)

    # Build document content
    tags_str = "\n".join([f"  - {tag}" for tag in template["tags"]])

    sections = ""
    for section in template["sections"]:
        sections += f"\n## {section}\n\n（请填写）\n"

    document = f"""---
date: {date_str}
tags:
{tags_str}
type: {template_type}
template: {template["name"]}
status: draft
---

# {title}

> 创建日期：{date_str}
> 模板类型：{template["name"]}
> 状态：草稿

{sections}
---

*此文档由知识库助手输出工坊生成*
"""

    # Save file
    filename = f"{date_str}_{title[:30]}.md"
    filepath = os.path.join(folder, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(document)

    print(f"[OUTPUT] Created: {template['folder']}/{filename}", flush=True)
    return filepath


async def assess_output_quality(content: str, template_type: str = "paper") -> Dict:
    """Assess the quality of an output document."""
    prompt_template = QUALITY_PROMPTS.get(template_type)
    if not prompt_template:
        return {"error": "No quality assessment template for this type"}

    prompt = prompt_template.format(content=content[:3000])

    try:
        messages = [{"role": "user", "content": prompt}]
        response = await chat_ollama(messages)

        # Parse JSON response
        import json
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(response[start:end])
            return result
    except Exception as e:
        return {"error": f"Quality assessment failed: {e}"}

    return {"error": "Failed to parse quality assessment"}


def track_output_input(output_path: str, input_sources: List[str]) -> Dict:
    """Track the relationship between output and input sources."""
    # Read output file
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Add source tracking to frontmatter
        if content.startswith("---"):
            # Insert source tracking after frontmatter
            source_section = f"\n## 输入来源\n\n"
            for source in input_sources:
                source_section += f"- [[{source}]]\n"

            # Find end of frontmatter
            end_frontmatter = content.find("---", 3)
            if end_frontmatter > 0:
                content = content[:end_frontmatter] + source_section + content[end_frontmatter:]

                # Write back
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return {"success": True, "sources_tracked": len(input_sources)}
    except Exception as e:
        return {"error": f"Failed to track sources: {e}"}

    return {"error": "Invalid document format"}


def get_output_stats() -> Dict:
    """Get statistics about output documents."""
    stats = {
        "total": 0,
        "by_type": {},
    }

    for template_type, template in OUTPUT_TEMPLATES.items():
        folder = os.path.join(VAULT_PATH, template["folder"])
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith(".md")]
            stats["by_type"][template_type] = len(files)
            stats["total"] += len(files)

    return stats
