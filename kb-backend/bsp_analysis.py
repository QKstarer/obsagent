"""
BSP sequencing analysis integration.
Provides entry points for CRISPResso/Bismark analysis and records results.
Integrates methylation_analyzer.py for CpG/non-CpG methylation analysis.
"""
import os
import sys
import time
import json
from typing import Dict, List, Optional
from config import VAULT_PATH

# Import methylation analyzer
sys.path.insert(0, os.path.dirname(__file__))
try:
    from methylation_analyzer import (
        discover_samples,
        analyze_single_sample,
        get_sample_id_from_folder,
        write_summary_csv,
        write_detailed_report,
    )
    METHYLATION_ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"[BSP] Warning: methylation_analyzer not available: {e}", flush=True)
    METHYLATION_ANALYZER_AVAILABLE = False

BSP_DIR = os.path.join(VAULT_PATH, "02_知识加工区", "实验方法库", "BSP测序分析")
os.makedirs(BSP_DIR, exist_ok=True)

RESULTS_DIR = os.path.join(VAULT_PATH, "02_知识加工区", "实验结果分析")
os.makedirs(RESULTS_DIR, exist_ok=True)

# CRISPResso analysis template for Ubuntu
CRISPRESSO_SCRIPT = """#!/bin/bash
# CRISPResso 分析脚本
# 使用方法：chmod +x run_crispresso.sh && ./run_crispresso.sh

# -------------------------- 参数设置 --------------------------
# 输入文件
FASTQ_R1="$1"
FASTQ_R2="$2"
REFERENCE="$3"
OUTPUT_DIR="${4:-crispresso_output}"

# CRISPResso 参数
WINDOW_SIZE=10
MINIMAL_AVERAGE_READ_QUALITY=0
MIN_SPACING=1
MAX_R1_CONSECUTIVE_END=1
MAX_R2_CONSECUTIVE_END=1
# -------------------------------------------------------------

echo "========================================="
echo "CRISPResso 分析开始"
echo "R1: ${FASTQ_R1}"
echo "R2: ${FASTQ_R2}"
echo "参考序列: ${REFERENCE}"
echo "输出目录: ${OUTPUT_DIR}"
echo "========================================="

# 运行 CRISPResso
CRISPResso \
    --fastq_r1 ${FASTQ_R1} \
    --fastq_r2 ${FASTQ_R2} \
    --amplicon_seq ${REFERENCE} \
    --output_folder ${OUTPUT_DIR} \
    --window_size ${WINDOW_SIZE} \
    --minimal_average_read_quality ${MINIMAL_AVERAGE_READ_QUALITY} \
    --min_spacing ${MIN_SPACING} \
    --max_R1_consecutive_end ${MAX_R1_CONSECUTIVE_END} \
    --max_R2_consecutive_end ${MAX_R2_CONSECUTIVE_END} \
    --exclude_bp_from_left 5 \
    --exclude_bp_from_right 5

echo "========================================="
echo "分析完成！结果保存在: ${OUTPUT_DIR}"
echo "========================================="
"""

# Bismark analysis template for Ubuntu
BISMARK_SCRIPT = """#!/bin/bash
# Bismark BSP 分析脚本
# 使用方法：chmod +x run_bismark.sh && ./run_bismark.sh

# -------------------------- 参数设置 --------------------------
FASTQ_DIR="$1"
REF_DIR="$2"
OUTPUT_DIR="${3:-bismark_output}"
THREADS="${4:-8}"
# -------------------------------------------------------------

echo "========================================="
echo "Bismark BSP 分析开始"
echo "FASTQ 目录: ${FASTQ_DIR}"
echo "参考序列目录: ${REF_DIR}"
echo "输出目录: ${OUTPUT_DIR}"
echo "线程数: ${THREADS}"
echo "========================================="

mkdir -p ${OUTPUT_DIR}/align
mkdir -p ${OUTPUT_DIR}/methylation

# 步骤 1: 构建索引
echo "[1/3] 构建 Bismark 索引..."
bismark_genome_preparation --bowtie2 ${REF_DIR}

# 步骤 2: 批量比对
echo "[2/3] 批量比对..."
for R1 in ${FASTQ_DIR}/*_R1.fastq.gz; do
    SAMPLE=$(basename ${R1} _R1.fastq.gz)
    R2=${FASTQ_DIR}/${SAMPLE}_R2.fastq.gz

    if [ ! -f ${R2} ]; then
        echo "警告: ${SAMPLE} 的 R2 文件不存在，跳过"
        continue
    fi

    echo "比对样品: ${SAMPLE}"
    bismark \\
        -1 ${R1} -2 ${R2} \\
        --genome ${REF_DIR} \\
        -o ${OUTPUT_DIR}/align \\
        -p ${THREADS} \\
        --name ${SAMPLE} \\
        --non_directional
done

# 步骤 3: 提取甲基化
echo "[3/3] 提取甲基化位点..."
for BAM in ${OUTPUT_DIR}/align/*.bam; do
    echo "提取: $(basename ${BAM})"
    bismark_methylation_extractor \\
        --paired-end --gzip --bedGraph --CX \\
        -o ${OUTPUT_DIR}/methylation \\
        ${BAM}
done

echo "========================================="
echo "分析完成！"
echo "比对结果: ${OUTPUT_DIR}/align"
echo "甲基化结果: ${OUTPUT_DIR}/methylation"
echo "========================================="
"""

RESULT_TEMPLATE = """---
ai_processed: true
date: {date}
tags:
  - BSP测序
  - 实验结果
  - {gene}
type: experiment-result
---

# BSP 测序分析结果 - {gene}

> 分析日期：{date}
> 分析工具：{tool}

## 实验信息

- **靶基因**：[[{gene}]]
- **样品数量**：{sample_count}
- **分析工具**：{tool}
- **参考序列**：{reference}

## 分析结果

### 甲基化编辑效率

{efficiency_table}

### 关键发现

{key_findings}

## 原始数据

- CRISPResso 输出：`{crispresso_dir}`
- 甲基化报告：`{methylation_report}`

## 相关概念

- [[BSP测序]]
- [[亚硫酸氢盐测序]]
- [[{gene}]]

---
*此结果由知识库助手记录*
"""


def get_analysis_scripts() -> Dict[str, str]:
    """Get analysis scripts for download/copy."""
    return {
        "crispresso": CRISPRESSO_SCRIPT,
        "bismark": BISMARK_SCRIPT,
    }


def create_analysis_entry(gene: str, tool: str = "CRISPResso", **kwargs) -> str:
    """Create an analysis entry point in Obsidian."""
    date_str = time.strftime("%Y-%m-%d")
    filename = f"{date_str}_{gene}_BSP分析.md"
    filepath = os.path.join(BSP_DIR, filename)

    content = f"""---
date: {date_str}
tags:
  - BSP测序
  - 分析入口
  - {gene}
type: analysis-entry
---

# {gene} BSP 测序分析

> 创建日期：{date_str}

## 分析状态

- [ ] 数据准备完成
- [ ] CRISPResso/Bismark 分析完成
- [ ] 结果整理完成
- [ ] 结果录入知识库

## 分析参数

- **靶基因**：[[{gene}]]
- **分析工具**：{tool}
- **样品数量**：{kwargs.get('sample_count', '待填写')}
- **参考序列**：{kwargs.get('reference', '待填写')}

## 分析步骤

### Ubuntu 环境分析

```bash
# 1. 进入分析环境
conda activate bsp_analysis

# 2. 运行 CRISPResso 分析
chmod +x run_crispresso.sh
./run_crispresso.sh R1.fastq.gz R2.fastq.gz reference_sequence

# 3. 运行 Bismark 分析（如需要）
chmod +x run_bismark.sh
./run_bismark.sh /path/to/fastq /path/to/reference
```

## 结果记录

分析完成后，请将结果记录在此处：

| 样品 | 对照组甲基化率 | 实验组甲基化率 | 编辑效率 |
|------|---------------|---------------|---------|
| S1 | | | |
| S2 | | | |
| S3 | | | |

## 相关文件

- [[模板_sgRNA]]
- [[BSP测序]]

---
*分析完成后请更新此文件*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[BSP] Created entry: {filename}", flush=True)
    return filepath


def record_analysis_result(gene: str, tool: str, results: Dict) -> str:
    """Record analysis results."""
    date_str = time.strftime("%Y-%m-%d")

    # Build efficiency table
    efficiency_table = "| 样品 | 对照组 | 实验组 | 编辑效率 |\n|------|--------|--------|----------|\n"
    for sample in results.get("samples", []):
        efficiency_table += f"| {sample['name']} | {sample['con']:.1%} | {sample['exp']:.1%} | {sample['efficiency']:.1%} |\n"

    # Build key findings
    key_findings = ""
    for finding in results.get("findings", []):
        key_findings += f"- {finding}\n"

    content = RESULT_TEMPLATE.format(
        date=date_str,
        gene=gene,
        tool=tool,
        sample_count=results.get("sample_count", 0),
        reference=results.get("reference", ""),
        efficiency_table=efficiency_table,
        key_findings=key_findings or "- （待补充）",
        crispresso_dir=results.get("crispresso_dir", ""),
        methylation_report=results.get("methylation_report", ""),
    )

    filename = f"{date_str}_{gene}_BSP结果.md"
    filepath = os.path.join(RESULTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[BSP] Recorded result: {filename}", flush=True)
    return filepath


def get_bsp_stats() -> Dict:
    """Get BSP analysis statistics."""
    entries = [f for f in os.listdir(BSP_DIR) if f.endswith(".md") and not f.startswith("模板")] if os.path.exists(BSP_DIR) else []
    results = [f for f in os.listdir(RESULTS_DIR) if "BSP" in f and f.endswith(".md")] if os.path.exists(RESULTS_DIR) else []

    return {
        "analysis_entries": len(entries),
        "completed_results": len(results),
        "recent_entries": entries[-5:],
        "recent_results": results[-5:],
        "methylation_analyzer_available": METHYLATION_ANALYZER_AVAILABLE,
    }


def run_methylation_analysis(input_dir: str, output_dir: str, sample_range: Optional[str] = None) -> Dict:
    """
    Run methylation analysis on CRISPResso output folders.

    Args:
        input_dir: Directory containing CRISPResso output folders
        output_dir: Directory to save results
        sample_range: Sample range (e.g., "419-504" or "419,420,421")

    Returns:
        Dict with analysis results
    """
    if not METHYLATION_ANALYZER_AVAILABLE:
        return {"error": "Methylation analyzer not available"}

    if not os.path.isdir(input_dir):
        return {"error": f"Input directory not found: {input_dir}"}

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Parse sample IDs
    sample_ids = None
    if sample_range:
        if '-' in sample_range:
            parts = sample_range.split('-')
            start = int(parts[0])
            end = int(parts[1])
            sample_ids = [f"S{i}" for i in range(start, end + 1)]
        elif ',' in sample_range:
            sample_ids = [f"S{x.strip()}" for x in sample_range.split(',') if x.strip().isdigit()]

    # Discover samples
    sample_folders = discover_samples(input_dir, sample_ids)

    if not sample_folders:
        return {"error": "No CRISPResso sample folders found"}

    # Analyze all samples
    results = []
    for sf in sample_folders:
        sid = get_sample_id_from_folder(sf)
        result = analyze_single_sample(sf)

        if result:
            results.append(result)
            # Write detailed report
            report_path = os.path.join(output_dir, f"{sid}_methylation_report.txt")
            write_detailed_report(result, report_path)

    if not results:
        return {"error": "No samples could be analyzed successfully"}

    # Write summary CSV
    summary_path = os.path.join(output_dir, "methylation_summary.csv")
    write_summary_csv(results, summary_path)

    # Generate summary statistics
    cpg_meth_avg = sum(r['cpg_methylation_quant_pct'] for r in results) / len(results)
    non_cpg_meth_avg = sum(r['non_cpg_methylation_quant_pct'] for r in results) / len(results)

    return {
        "success": True,
        "samples_analyzed": len(results),
        "summary_csv": summary_path,
        "output_dir": output_dir,
        "avg_cpg_methylation": round(cpg_meth_avg, 2),
        "avg_non_cpg_methylation": round(non_cpg_meth_avg, 2),
        "sample_results": [
            {
                "sample": r['sample_name'],
                "cpg_meth": r['cpg_methylation_quant_pct'],
                "non_cpg_meth": r['non_cpg_methylation_quant_pct'],
            }
            for r in results
        ],
    }


def record_methylation_to_vault(gene: str, analysis_result: Dict) -> str:
    """Record methylation analysis results to the vault."""
    date_str = time.strftime("%Y-%m-%d")

    # Build sample table
    sample_table = "| 样品 | CpG 甲基化率 | Non-CpG 甲基化率 |\n|------|-------------|------------------|\n"
    for s in analysis_result.get("sample_results", []):
        sample_table += f"| {s['sample']} | {s['cpg_meth']:.1f}% | {s['non_cpg_meth']:.1f}% |\n"

    content = f"""---
ai_processed: true
date: {date_str}
tags:
  - BSP测序
  - 甲基化分析
  - {gene}
type: experiment-result
---

# {gene} 甲基化分析结果

> 分析日期：{date_str}
> 分析工具：CRISPResso + Methylation Analyzer

## 分析概览

- **分析样品数**：{analysis_result.get('samples_analyzed', 0)}
- **平均 CpG 甲基化率**：{analysis_result.get('avg_cpg_methylation', 0):.1f}%
- **平均 Non-CpG 甲基化率**：{analysis_result.get('avg_non_cpg_methylation', 0):.1f}%

## 样品结果

{sample_table}

## 输出文件

- **汇总 CSV**：`{analysis_result.get('summary_csv', '')}`
- **详细报告**：`{analysis_result.get('output_dir', '')}/*_methylation_report.txt`

## 相关概念

- [[BSP测序]]
- [[亚硫酸氢盐测序]]
- [[{gene}]]

---
*此结果由知识库助手自动记录*
"""

    filename = f"{date_str}_{gene}_甲基化结果.md"
    filepath = os.path.join(RESULTS_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[BSP] Recorded methylation result: {filename}", flush=True)
    return filepath
