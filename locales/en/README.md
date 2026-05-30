# KB Assistant

> Full-cycle knowledge management plugin for Obsidian, powered by local LLMs

[中文版](../zh/README.md)

### Features

| Feature | Description |
|---------|-------------|
| **💬 Smart Q&A** | RAG chat with source citations |
| **🔍 Hybrid Search** | Vector semantic + keyword matching |
| **🧠 Knowledge Graph** | Auto-build concept networks from `[[wikilinks]]` |
| **⚡ Auto Indexing** | File watcher with incremental updates |
| **📝 Guided Input** | Interactive wizard for structured documents |
| **📥 Quick Capture** | Inbox mode for ideas |
| **🏷️ Auto Classification** | Content categorization + tag suggestions |
| **⚠️ Conflict Detection** | Find contradictions between notes |
| **✍️ Writing Assistant** | Generate methods, results, discussion |
| **📈 Progress Tracker** | Weekly statistics + auto reports |
| **🖼️ Image Processing** | Extract text from images |
| **💾 Knowledge Cache** | Instant answers for frequent queries |

### Quick Start

```bash
# 1. Pull models
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text

# 2. Install plugin
cp -r kb-plugin/ <Vault>/.obsidian/plugins/kb-plugin/

# 3. Start backend
cd kb-backend
pip install -r requirements.txt
set LANG=en
python main.py
```

### Configuration

| Env Variable | Default | Description |
|-------------|---------|-------------|
| `OBSIDIAN_VAULT` | *(required)* | Vault path |
| `LANG` | `en` | Language: `zh` / `en` |
| `LLM_PROVIDER` | `auto` | `ollama` / `siliconflow` / `deepseek` / `auto` |
| `OLLAMA_LLM` | `deepseek-r1:7b` | Chat model |
| `OLLAMA_EMBED` | `nomic-embed-text` | Embedding model |
| `DEEPSEEK_KEY` | *(empty)* | DeepSeek API key |
| `GRAPH_SAVE_TO_VAULT` | `false` | Save graph to vault |

### Supported Models

| Chat | Embed |
|------|-------|
| `qwen2.5:3b/7b/14b/32b/72b` | `nomic-embed-text` (768d) |
| `deepseek-r1:1.5b/7b/14b/32b/70b` | `mxbai-embed-large` (1024d) |
| `llama3.1:8b/70b` · `mistral:7b` | `bge-m3` (SiliconFlow) |
| `gemma2:9b` · `phi3:3.8b` · ... | `gte-qwen2` (SiliconFlow) |

> All Ollama models supported. Set `OLLAMA_LLM` to switch.

### Lightweight Picks

| RAM | Model | Usage |
|-----|-------|-------|
| 8GB | `deepseek-r1:1.5b` | ~1.5GB |
| 8GB | `qwen2.5:3b` | ~2.5GB |
| 16GB | `deepseek-r1:7b` | ~5GB |
| 16GB | `qwen2.5:7b` | ~5GB |
| 32GB | `deepseek-r1:14b` | ~9GB |

### LLM Provider Adaptation

| Provider | Setup | Best For |
|----------|-------|----------|
| **Ollama** (default) | Install Ollama, pull model | Privacy, offline, no API cost |
| **DeepSeek** | `set DEEPSEEK_KEY=sk-xxx` | Best Chinese reasoning |
| **SiliconFlow** | `set SILICONFLOW_KEY=sk-xxx` | Multi-model cloud access |
| **Auto** | `set LLM_PROVIDER=auto` | Fallback chain: Ollama → SF → DeepSeek |

```bash
# Local only (free, private)
set LLM_PROVIDER=ollama
set OLLAMA_LLM=deepseek-r1:7b

# Cloud only (pay per use)
set LLM_PROVIDER=deepseek
set DEEPSEEK_KEY=sk-your-key

# Hybrid (local first, cloud fallback)
set LLM_PROVIDER=auto
```

> No GPU needed — Ollama runs on CPU.

### License

[Apache 2.0](../../LICENSE)
