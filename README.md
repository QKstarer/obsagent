# KB Assistant

> Full-cycle knowledge management plugin for Obsidian, powered by local LLMs

[![Obsidian](https://img.shields.io/badge/Obsidian-%E2%89%A5%201.0.0-7C3AED?logo=obsidian)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-%E2%89%A5%203.9-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**[中文文档](locales/zh/README.md)** · **[English](locales/en/README.md)**

### What It Does

KB Assistant goes beyond simple Q&A — it automatically organizes, processes, and connects your knowledge using local LLMs.

### Features

| Feature | Description |
|---------|-------------|
| **💬 Smart Q&A** | RAG chat with source citations and concept links |
| **🔍 Hybrid Search** | Vector semantic + keyword exact matching |
| **🧠 Knowledge Graph** | Auto-build concept networks from `[[wikilinks]]` |
| **⚡ Auto Indexing** | File watcher with incremental updates |
| **📝 Guided Input** | Interactive wizard for structured documents |
| **📥 Quick Capture** | Inbox mode for ideas on the fly |
| **🏷️ Auto Classification** | Content categorization and tag suggestions |
| **⚠️ Conflict Detection** | Find contradictions between notes |
| **✍️ Writing Assistant** | Generate methods, results, discussion sections |
| **📈 Progress Tracker** | Weekly statistics and report generation |
| **🖼️ Image Processing** | Extract text from images to documents |
| **💾 Knowledge Cache** | Frequently asked Q&A auto-cached for instant answers |

### Architecture

```
┌───────────────────────────────────────────────────┐
│                  Obsidian Plugin                    │
│  Chat UI · Guided Input · Inbox · Commands          │
└──────────────────────┬────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼────────────────────────────┐
│                  Python Backend                     │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ RAG      │ │ KG       │ │ Cache    │           │
│  │ Retriever│ │ Retriever│ │ Layer    │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Content  │ │ Writing  │ │ Conflict │           │
│  │ Processor│ │ Assistant│ │ Detector │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ File     │ │ ChromaDB │ │ Ollama / │           │
│  │ Watcher  │ │ VectorDB │ │ DeepSeek │           │
│  └──────────┘ └──────────┘ └──────────┘           │
└───────────────────────────────────────────────────┘
```

### Retrieval Pipeline

```
Query → ① Cache hit? → Return instantly
        ↓ miss
        ② Vector search + Keyword search
        ③ Knowledge graph context extraction
        ④ Merge context → LLM generates answer
        ⑤ Cache answer for next time
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | TypeScript + Obsidian API |
| Backend | Python + FastAPI |
| Vector DB | ChromaDB |
| Embeddings | nomic-embed-text / bge-m3 |
| LLM | deepseek-r1 (Ollama local / DeepSeek API) |
| Knowledge Graph | Auto-built from `[[wikilinks]]` |
| Cache | JSON-based with LRU cleanup |

### Quick Start

**Prerequisites:** Obsidian ≥ 1.0.0, Python ≥ 3.9, [Ollama](https://ollama.ai)

```bash
# 1. Pull models
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text

# 2. Install plugin
cp -r kb-plugin/ <Vault>/.obsidian/plugins/kb-plugin/

# 3. Start backend
cd kb-backend
pip install -r requirements.txt
python main.py
```

### Configuration

| Env Variable | Default | Description |
|-------------|---------|-------------|
| `OBSIDIAN_VAULT` | *(required)* | Vault path |
| `LLM_PROVIDER` | `auto` | `ollama` / `siliconflow` / `deepseek` / `auto` |
| `OLLAMA_LLM` | `deepseek-r1:7b` | Chat model |
| `OLLAMA_EMBED` | `nomic-embed-text` | Embedding model |
| `DEEPSEEK_KEY` | *(empty)* | DeepSeek API key |
| `SILICONFLOW_KEY` | *(empty)* | SiliconFlow API key |
| `CHUNK_SIZE` | `500` | Text chunk size |
| `TOP_K` | `5` | Search results |

### Supported Models

| Chat | Embed |
|------|-------|
| `qwen2.5:3b/7b/14b/32b/72b` | `nomic-embed-text` (768d) |
| `deepseek-r1:1.5b/7b/14b/32b/70b` | `mxbai-embed-large` (1024d) |
| `llama3.1:8b/70b` · `mistral:7b` | `bge-m3` (SiliconFlow) |
| `gemma2:9b` · `phi3:3.8b` · ... | `gte-qwen2` (SiliconFlow) |

> All Ollama models supported. Set `OLLAMA_LLM` to switch.

#### Lightweight Picks (iGPU / No Discrete GPU)

| Hardware | Model | RAM | Notes |
|----------|-------|-----|-------|
| 8GB | `deepseek-r1:1.5b` | ~1.5GB | Smallest, fastest |
| 8GB | `qwen2.5:3b` | ~2.5GB | Fast daily Q&A |
| 16GB | `deepseek-r1:7b` | ~5GB | **Recommended** |
| 16GB | `qwen2.5:7b` | ~5GB | Balanced |
| 32GB | `deepseek-r1:14b` | ~9GB | Deep reasoning |
| 32GB | `qwen2.5:14b` | ~9GB | High quality |

> 💡 No GPU needed — Ollama runs on CPU. 7b models respond in ~2-5s on 16GB machines.

### API Endpoints

| Category | Endpoints |
|----------|-----------|
| Core | `/api/chat`, `/api/chat/stream`, `/api/search`, `/api/index` |
| Knowledge Graph | `/api/kg`, `/api/kg/related`, `/api/graph/*` |
| Cache | `/api/cache`, `/api/cache/clear` |
| Content | `/api/classify`, `/api/links/*` |
| Writing | `/api/writing/methods`, `/api/writing/results`, `/api/writing/discussion` |
| System | `/api/health`, `/api/status`, `/api/progress/*`, `/api/logs` |

### Auto Features

| Feature | Trigger | Description |
|---------|---------|-------------|
| Incremental Index | File change | 10s debounce, auto-update vectors |
| KG Build | 30s check | Incremental update on file changes |
| Cache | Every query | Frequently asked Q&A cached |
| Conflict Detection | On startup | Scan note contradictions |
| Progress Report | Weekly | Statistics and report |

### Project Structure

```
obsagent/
├── kb-plugin/                # Obsidian Plugin
│   ├── main.js
│   ├── api.js
│   ├── styles.css
│   └── manifest.json
├── kb-backend/               # Python Backend
│   ├── main.py               # FastAPI (30+ endpoints)
│   ├── config.py             # Configuration
│   ├── locale.py             # i18n (zh/en)
│   ├── llm.py                # LLM providers (Ollama/SF/DeepSeek)
│   ├── retriever.py          # RAG + KG + Cache pipeline
│   ├── kg_retriever.py       # Knowledge graph (incremental)
│   ├── knowledge_cache.py    # Q&A cache
│   ├── vectorstore.py        # ChromaDB
│   ├── embeddings.py         # Embedding models
│   ├── indexer.py            # Index management
│   ├── watcher.py            # File watcher
│   ├── knowledge_graph.py    # Graph generation
│   ├── conflict_detector.py  # Conflict detection
│   ├── content_classifier.py # Auto classification
│   ├── writing_assistant.py  # Writing assistant
│   ├── progress_tracker.py   # Progress tracking
│   ├── conversation_saver.py # Chat history
│   ├── failure_tracker.py    # Failure extraction
│   ├── image_processor.py    # Image processing
│   └── requirements.txt
├── locales/                  # Language files
│   ├── zh/                   # Chinese
│   │   ├── README.md
│   │   ├── system_prompt.txt
│   │   └── install.bat
│   └── en/                   # English
│       ├── README.md
│       ├── system_prompt.txt
│       └── install.bat
├── docs/                     # GitHub Pages
├── README.md
├── LICENSE                   # Apache 2.0
└── .gitignore
```

## License

[Apache 2.0](LICENSE) — Free to use and modify with attribution.
