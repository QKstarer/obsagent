import os
from pathlib import Path

# ─── 语言设置 ───
# 可选值: "zh" | "en"
LANG = os.environ.get("LANG", "zh").lower()

# ─── 知识图谱自动写入 vault ───
# true  — 每6小时自动在 vault 中生成 .md 图谱文件（会创建文件）
# false — 仅内存中构建，不写入 vault（默认，推荐）
GRAPH_SAVE_TO_VAULT = os.environ.get("GRAPH_SAVE_TO_VAULT", "false").lower() == "true"

VAULT_PATH = os.environ.get("OBSIDIAN_VAULT", "")
CHROMA_PATH = os.environ.get("CHROMA_PATH", os.path.join(os.path.dirname(__file__), "chroma_db"))

# ─── Ollama (本地推理) ───
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
OLLAMA_LLM = os.environ.get("OLLAMA_LLM", "qwen2.5:7b")
OLLAMA_EMBED = os.environ.get("OLLAMA_EMBED", "nomic-embed-text")

# ─── SiliconFlow (云端备选) ───
SILICONFLOW_API = os.environ.get("SILICONFLOW_API", "https://api.siliconflow.cn/v1")
SILICONFLOW_KEY = os.environ.get("SILICONFLOW_KEY", "")
SILICONFLOW_EMBED_MODEL = os.environ.get("SILICONFLOW_EMBED_MODEL", "BAAI/bge-m3")
SILICONFLOW_LLM_MODEL = os.environ.get("SILICONFLOW_LLM_MODEL", "deepseek-ai/DeepSeek-R1")

# ─── DeepSeek (云端直连) ───
DEEPSEEK_API = os.environ.get("DEEPSEEK_API", "https://api.deepseek.com")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# ─── 模型选择策略 ───
# 可选值: "ollama" | "siliconflow" | "deepseek" | "auto"
# ollama      — 仅用本地 Ollama
# siliconflow — 仅用 SiliconFlow 云端
# deepseek    — 仅用 DeepSeek 官方 API
# auto        — 优先 Ollama，失败回退 SiliconFlow → DeepSeek（默认）
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto")

# ─── 推荐模型配置 ───
# 聊天模型 (从快到强排列):
#   qwen2.5:3b        — 最快，适合低配机器
#   qwen2.5:7b        — 均衡，默认推荐
#   qwen2.5:14b       — 更强，需要 16GB+ 内存
#   deepseek-r1:7b    — 推理能力强
#   llama3.1:8b       — 英文优秀
#   mistral:7b        — 欧洲语言支持好
#
# 嵌入模型:
#   nomic-embed-text  — 轻量，768维（默认）
#   mxbai-embed-large — 更精确，1024维
#   bge-m3            — 多语言最强，需 SiliconFlow
#
# 切换方式: 设置环境变量，例如:
#   set OLLAMA_LLM=qwen2.5:14b
#   set LLM_PROVIDER=ollama

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "50"))
TOP_K = int(os.environ.get("TOP_K", "5"))
