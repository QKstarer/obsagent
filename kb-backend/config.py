import os
from pathlib import Path

VAULT_PATH = os.environ.get("OBSIDIAN_VAULT", r"D:\research\Obsidian\paperbell")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
OLLAMA_LLM = os.environ.get("OLLAMA_LLM", "qwen2.5:7b")
OLLAMA_EMBED = os.environ.get("OLLAMA_EMBED", "nomic-embed-text")
SILICONFLOW_API = os.environ.get("SILICONFLOW_API", "https://api.siliconflow.cn/v1")
SILICONFLOW_KEY = os.environ.get("SILICONFLOW_KEY", "")
SILICONFLOW_EMBED_MODEL = "BAAI/bge-m3"
SILICONFLOW_LLM_MODEL = "deepseek-ai/DeepSeek-R1"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5
