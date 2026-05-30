"""
Content classification module for automatic categorization.
Automatically routes content to appropriate directories.
"""
import os
import re
from typing import Dict, List, Tuple
from config import VAULT_PATH

# Classification rules based on keywords and patterns
CLASSIFICATION_RULES = {
    "experiment": {
        "keywords": ["实验", "protocol", "步骤", "试剂", "细胞", "pcr", "western",
                     "转染", "转导", "培养", "离心", "提取", "纯化", "检测"],
        "folder": "01_输入区/实验记录",
        "tags": ["实验记录"],
        "priority": 1,
    },
    "literature": {
        "keywords": ["论文", "研究", "发现", "结论", "摘要", "abstract", "journal",
                     "doi", "作者", "发表", "期刊", "引用"],
        "folder": "01_输入区/文献笔记",
        "tags": ["文献笔记"],
        "priority": 2,
    },
    "concept": {
        "keywords": ["crispr", "甲基化", "表观遗传", "dnmt", "cas9", "基因",
                     "蛋白", "酶", "结构域", "通路", "机制"],
        "folder": "02_知识加工区/概念卡片",
        "tags": ["概念"],
        "priority": 3,
    },
    "protocol": {
        "keywords": ["方案", "protocol", "方法", "操作", "流程", "sop",
                     "指南", "教程", "说明"],
        "folder": "02_知识加工区/实验方法库",
        "tags": ["实验方法"],
        "priority": 4,
    },
    "problem": {
        "keywords": ["问题", "失败", "错误", "解决", "排查", "故障",
                     "异常", "bug", "troubleshoot"],
        "folder": "02_知识加工区/问题与解决方案",
        "tags": ["问题案例"],
        "priority": 5,
    },
    "idea": {
        "keywords": ["想法", "灵感", "思考", "思路", "方案", "计划",
                     "todo", "待办", "目标"],
        "folder": "01_输入区/每日笔记",
        "tags": ["灵感想法"],
        "priority": 6,
    },
    "note": {
        "keywords": ["笔记", "学习", "课程", "教程", "总结", "复习"],
        "folder": "01_输入区/每日笔记",
        "tags": ["学习笔记"],
        "priority": 7,
    },
}

# Priority order for classification (lower number = higher priority)
PRIORITY_ORDER = ["experiment", "literature", "concept", "protocol", "problem", "idea", "note"]


def classify_content(text: str, filename: str = "") -> Dict:
    """Classify content based on keywords and patterns."""
    text_lower = text.lower()
    filename_lower = filename.lower()

    scores = {}

    for category, rules in CLASSIFICATION_RULES.items():
        score = 0
        for keyword in rules["keywords"]:
            if keyword in text_lower or keyword in filename_lower:
                score += 1
        if score > 0:
            scores[category] = score

    if not scores:
        # Default to note if no match
        return {
            "category": "note",
            "folder": CLASSIFICATION_RULES["note"]["folder"],
            "tags": CLASSIFICATION_RULES["note"]["tags"],
            "confidence": 0.5,
        }

    # Get the category with highest score
    best_category = max(scores, key=scores.get)
    max_score = scores[best_category]

    # Calculate confidence (0-1)
    total_possible = len(CLASSIFICATION_RULES[best_category]["keywords"])
    confidence = min(max_score / total_possible, 1.0)

    return {
        "category": best_category,
        "folder": CLASSIFICATION_RULES[best_category]["folder"],
        "tags": CLASSIFICATION_RULES[best_category]["tags"],
        "confidence": confidence,
        "scores": scores,
    }


def get_suggested_tags(text: str, category: str) -> List[str]:
    """Suggest additional tags based on content analysis."""
    text_lower = text.lower()
    tags = CLASSIFICATION_RULES.get(category, {}).get("tags", []).copy()

    # Add specific tags based on content
    tag_keywords = {
        "#CRISPRoff": ["crisproff", "crispr-off"],
        "#甲基化编辑": ["甲基化", "methylation", "dnmt"],
        "#BSP测序": ["bsp", "亚硫酸氢盐", "bisulfite"],
        "#分子克隆": ["克隆", "clone", "载体", "质粒"],
        "#细胞培养": ["细胞", "cell", "培养", "culture"],
        "#sgRNA设计": ["sgrna", "guide rna"],
        "#实验失败": ["失败", "fail", "error"],
        "#文献综述": ["综述", "review", "总结"],
        "#课题进展": ["进展", "progress", "进度"],
    }

    for tag, keywords in tag_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                if tag not in tags:
                    tags.append(tag)
                break

    return tags


def suggest_folder(content_type: str, text: str) -> str:
    """Suggest the best folder for the content."""
    classification = classify_content(text)
    return classification["folder"]


def batch_classify(items: List[Dict]) -> List[Dict]:
    """Classify a batch of items."""
    results = []
    for item in items:
        text = item.get("text", "")
        filename = item.get("filename", "")
        classification = classify_content(text, filename)
        tags = get_suggested_tags(text, classification["category"])

        results.append({
            **item,
            "classification": classification,
            "suggested_tags": tags,
        })

    return results
