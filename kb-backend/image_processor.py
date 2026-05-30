"""
Image processing module using Ollama vision model.
"""
import os
import re
import time
import base64
from typing import Dict, List
from config import VAULT_PATH
from llm import chat_ollama
import httpx


async def extract_text_from_image(image_path: str) -> Dict:
    """Extract text from image using Ollama vision model."""
    if not os.path.exists(image_path):
        return {"error": f"Image not found: {image_path}"}

    try:
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # Call Ollama vision API
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "qwen2.5:7b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "请提取这张图片中的所有文字内容，保持原始格式。只输出文字，不要添加解释。",
                            "images": [image_data]
                        }
                    ],
                    "stream": False
                }
            )
            response.raise_for_status()
            result = response.json()
            text = result["message"]["content"]

            return {
                "success": True,
                "text": text,
                "line_count": len(text.split("\n")),
            }
    except Exception as e:
        return {"error": f"Vision processing failed: {e}"}


def format_ocr_text(raw_text: str) -> str:
    """Format OCR text: merge broken lines, fix punctuation, clear paragraphs."""
    lines = raw_text.split("\n")

    # Watermark patterns to filter out
    watermark_patterns = [
        r'^XIAOMI', r'^Redmi', r'^HUAWEI', r'^iPhone',
        r'^\d{4}[\.\-/]\d{2}[\.\-/]\d{2}',  # Dates like 2025.10.15
        r'^\d{2}:\d{2}$',  # Time like 21:58
        r'^\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}$',  # Full timestamp
        r'^Shot on', r'^MEIZU', r'^vivo', r'^OPPO',
        r'^\d+\s*$',  # Just numbers
    ]

    # Skip list
    skip_words = {"豆包", "内容由 Al 生成", "内容由AI生成", "专家》", "Al 创作",
                  "帮我写作", "发消息或按住说话。", "KBIs", "66", "0.14", "22:12",
                  "专家》", "Al", "创作", "5", "笔记属性"}

    def is_watermark(text: str) -> bool:
        for pattern in watermark_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        return False

    # Step 1: Filter and clean lines
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line in skip_words or len(line) < 2:
            continue
        if is_watermark(line):
            continue
        # Remove leading noise (numbers/dots at start)
        cleaned_line = re.sub(r'^[\d\.\s:：]+', '', line).strip()
        if cleaned_line and len(cleaned_line) > 1:
            cleaned.append(cleaned_line)

    # Step 2: Merge broken lines into paragraphs
    paragraphs = []
    current_para = ""

    for line in cleaned:
        # Detect new paragraph markers
        is_new_para = (
            re.match(r'^[1-9][\.\、]', line) or          # Numbered items: 1. 2. 3.
            re.match(r'^[（(]\d+[)）]', line) or         # (1) (2)
            re.match(r'^[一二三四五六七八九十]+[\、.]', line) or  # Chinese numbers
            re.match(r'^#{1,3}\s', line) or              # Markdown headers
            (len(line) > 15 and not current_para)        # Long line as new para
        )

        if is_new_para and current_para:
            paragraphs.append(current_para)
            current_para = line
        else:
            # Merge with previous line if it looks like continuation
            if current_para and not line[0].isdigit():
                current_para += line
            else:
                current_para = line

    if current_para:
        paragraphs.append(current_para)

    # Step 3: Format each paragraph
    result = []
    for para in paragraphs:
        # Fix common OCR errors
        para = para.replace("。", "，").replace("；", "，")
        # Add proper spacing around numbers/letters
        para = re.sub(r'(\d)([^\d\s])', r'\1\2', para)
        para = re.sub(r'([^\s\d])(\d)', r'\1 \2', para)
        # Clean up
        para = re.sub(r'\s+', ' ', para).strip()
        if len(para) > 5:
            result.append(para)

    return "\n\n".join(result)


def generate_title_from_content(text: str, filename: str = "") -> str:
    """Generate a meaningful title from OCR content."""
    # Try to find a title-like line (first meaningful line)
    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        # Skip short lines and common patterns
        if len(line) < 5 or re.match(r'^[\d\.\s:：]+$', line):
            continue
        # Remove numbered prefixes
        title = re.sub(r'^[1-9][\.\、]\s*', '', line)
        title = re.sub(r'^[（(]\d+[)）]\s*', '', title)
        # Skip lines that look like content (too long or start with common words)
        if len(title) > 5 and len(title) < 60:
            return title

    # Fallback: use filename without extension and hash
    if filename:
        name = os.path.splitext(filename)[0]
        # If it looks like a hash, use "图片笔记"
        if len(name) > 20 or re.match(r'^[a-f0-9]+$', name):
            return "图片笔记"
        return name

    return "图片笔记"


def classify_content(text: str, filename: str = "") -> Dict:
    """Classify content using the content classifier module."""
    from content_classifier import classify_content as classifier_classify, get_suggested_tags

    classification = classifier_classify(text, filename)

    # Add OCR tag
    tags = classification["tags"].copy()
    tags.append("OCR")

    return {
        "folder": classification["folder"],
        "category": classification["category"],
        "tags": tags,
        "confidence": classification["confidence"],
    }


async def process_image_to_document(image_path: str, title: str = None) -> str:
    """Process image: OCR extract -> Format -> Classify -> Save."""
    # Step 1: OCR extract text
    ocr_result = extract_text_from_image(image_path)

    if "error" in ocr_result:
        return ocr_result["error"]

    raw_text = ocr_result["text"]

    if not raw_text.strip():
        return "未识别到文字内容"

    # Step 2: Format OCR text
    formatted_text = format_ocr_text(raw_text)

    # Step 3: Classify content
    classification = classify_content(formatted_text, os.path.basename(image_path))

    # Step 4: Generate title from content
    if not title:
        title = generate_title_from_content(formatted_text, os.path.basename(image_path))

    # Step 5: Save to appropriate folder
    date_str = time.strftime("%Y-%m-%d")
    output_dir = os.path.join(VAULT_PATH, classification["folder"])
    os.makedirs(output_dir, exist_ok=True)

    filename = f"{date_str}_{title[:30]}.md"
    filepath = os.path.join(output_dir, filename)

    # Build tags
    tags_str = "\n".join([f"  - {tag}" for tag in classification["tags"]])

    content = f"""---
date: {date_str}
tags:
{tags_str}
type: image-note
category: {classification["category"]}
source: {image_path}
---

# {title}

> 识别日期：{date_str}
> 来源图片：{os.path.basename(image_path)}
> 分类：{classification["category"]}

## 识别内容

{formatted_text}

---
*此文档由知识库助手自动识别生成*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[IMAGE] Document created: {classification['category']}/{filename}", flush=True)
    return filepath


async def process_multiple_images(image_paths: list) -> list:
    """Process multiple images."""
    results = []
    for path in image_paths:
        result = await process_image_to_document(path)
        results.append({"path": path, "result": result})
    return results
