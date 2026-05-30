# KB Assistant (知识库助手)

> 基于本地大语言模型的 Obsidian 知识管理全流程插件

[![Obsidian](https://img.shields.io/badge/Obsidian-%E2%89%A5%201.0.0-7C3AED?logo=obsidian)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-%E2%89%A5%203.9-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

[English](#english) | [中文](#中文)

---

## English

### What It Does

KB Assistant is a full-cycle knowledge management plugin for Obsidian, powered by local LLMs. It goes beyond simple Q&A — it automatically organizes, processes, and connects your knowledge.

### Core Features

| Feature | Description |
|---------|-------------|
| **💬 Smart Q&A** | RAG-based chat with source citations and concept links |
| **🔍 Hybrid Search** | Vector semantic + keyword exact matching |
| **⚡ Auto Indexing** | File watcher with incremental updates, auto-rebuild |
| **📝 Guided Input** | Interactive wizard to create structured documents |
| **📥 Quick Capture** | Inbox mode for capturing ideas on the fly |
| **🏷️ Auto Classification** | Content categorization and tag suggestions |
| **🔗 Entity Recognition** | Auto-detect genes, proteins, techniques; generate `[[links]]` |
| **⚠️ Conflict Detection** | Find contradictions between concept cards |
| **📊 Knowledge Graph** | Mermaid visualization of concept relationships |
| **✍️ Writing Assistant** | Generate methods, results, discussion sections |
| **📈 Progress Tracker** | Weekly work statistics and report generation |
| **🖼️ Image Processing** | Extract text from images to documents |
| **🧪 CRISPRoff KB** | Specialized gene editing knowledge base |
| **🧬 sgRNA Manager** | Design and track sgRNA records |
| **🔬 BSP Analysis** | Bisulfite sequencing analysis pipeline |
| **💡 Failure Tracker** | Auto-extract experiment failures from Q&A |
| **💬 Conversation Log** | Auto-save all chats with sources |

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
│  │ RAG      │ │ Content  │ │ Writing  │           │
│  │ Retriever│ │ Processor│ │ Assistant│           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Entity   │ │ Conflict │ │ Knowledge│           │
│  │ Recognizer│ │ Detector │ │ Graph    │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ File     │ │ ChromaDB │ │ Ollama / │           │
│  │ Watcher  │ │ VectorDB │ │ SiliconFlow│          │
│  └──────────┘ └──────────┘ └──────────┘           │
└───────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | TypeScript + Obsidian API |
| Backend | Python + FastAPI |
| Vector DB | ChromaDB |
| Embeddings | nomic-embed-text / bge-m3 |
| LLM | deepseek-r1 (Ollama 本地 / DeepSeek API) |
| File Watch | watchdog |

### Quick Start

**Prerequisites:** Obsidian ≥ 1.0.0, Python ≥ 3.9, [Ollama](https://ollama.ai)

```bash
# 1. Pull models
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text

# 2. Install plugin: copy kb-plugin/ to <Vault>/.obsidian/plugins/kb-plugin/

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
| `SILICONFLOW_KEY` | *(empty)* | Cloud API key |
| `CHUNK_SIZE` | `500` | Text chunk size |
| `TOP_K` | `5` | Search results |

### Supported Models

| Chat | Embed |
|------|-------|
| `qwen2.5:3b/7b/14b/32b/72b` | `nomic-embed-text` (768d) |
| `deepseek-r1:1.5b/7b/14b/32b/70b` | `mxbai-embed-large` (1024d) |
| `llama3.1:8b/70b` · `mistral:7b` | `bge-m3` (SiliconFlow) |
| `gemma2:9b` · `phi3:3.8b` · `...` | `gte-qwen2` (SiliconFlow) |

> All Ollama-supported models work. Set `OLLAMA_LLM` env var to switch.

#### Lightweight Picks (Integrated GPU / No Discrete GPU)

| Hardware | Model | RAM | Notes |
|----------|-------|-----|-------|
| 8GB RAM | `qwen2.5:3b` | ~2.5GB | Fastest, daily Q&A |
| 8GB RAM | `deepseek-r1:1.5b` | ~1.5GB | Smallest, basic reasoning |
| 16GB RAM | `qwen2.5:7b` | ~5GB | Balanced, **recommended** |
| 16GB RAM | `deepseek-r1:7b` | ~5GB | Stronger reasoning |
| 32GB RAM | `qwen2.5:14b` | ~9GB | High quality |
| 32GB RAM | `deepseek-r1:14b` | ~9GB | Deep reasoning |

> 💡 **iGPU users:** Ollama runs on CPU by default — no discrete GPU needed. 7b models respond in ~2-5s on 16GB machines.

### API Overview (30+ endpoints)

| Category | Endpoints |
|----------|-----------|
| Core | `/api/chat`, `/api/chat/stream`, `/api/search`, `/api/index` |
| Content | `/api/classify`, `/api/entities/*`, `/api/links/*` |
| Writing | `/api/writing/methods`, `/api/writing/results`, `/api/writing/discussion` |
| Knowledge | `/api/graph/*`, `/api/conflicts`, `/api/output/*` |
| Domain | `/api/sgrna/*`, `/api/bsp/*`, `/api/crisproff/*` |
| System | `/api/health`, `/api/status`, `/api/progress/*`, `/api/logs` |

---

## 中文

### 功能全景

KB Assistant 不只是问答工具——它是 Obsidian 的全流程知识管理助手。

| 功能 | 说明 |
|------|------|
| **💬 智能问答** | RAG 检索 + 流式输出，自动引用来源和概念链接 |
| **🔍 混合检索** | 向量语义 + 关键词精确匹配，双引擎融合 |
| **⚡ 自动索引** | 文件监控 + 增量更新，修改即生效 |
| **📝 引导输入** | 交互式向导，按模板创建实验记录、文献笔记等 |
| **📥 快速捕获** | 收件箱模式，随时记录灵感 |
| **🏷️ 自动分类** | 内容分类 + 标签推荐 |
| **⚠️ 冲突检测** | 发现概念卡片间的矛盾信息 |
| **📊 知识图谱** | Mermaid 可视化概念关联 |
| **✍️ 写作助手** | AI 生成方法、结果、讨论章节 |
| **📈 进度追踪** | 本周工作统计 + 自动周报 |
| **🖼️ 图片处理** | 图片文字提取，自动转为笔记 |
| **💡 失败追踪** | 从问答中自动提取失败案例 |
| **💬 对话日志** | 所有问答自动保存，含来源引用 |

### 技术栈

| 组件 | 技术 |
|------|------|
| 前端插件 | TypeScript + Obsidian API |
| 后端服务 | Python + FastAPI |
| 向量数据库 | ChromaDB |
| 嵌入模型 | nomic-embed-text (Ollama) / bge-m3 (SiliconFlow) |
| 大语言模型 | deepseek-r1 (Ollama 本地 / DeepSeek API) |
| 文件监控 | watchdog |

### 快速开始

**前置条件：** Obsidian ≥ 1.0.0, Python ≥ 3.9, [Ollama](https://ollama.ai)

```bash
# 1. 拉取模型
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text

# 2. 安装插件：复制 kb-plugin/ 到 <Vault>/.obsidian/plugins/kb-plugin/

# 3. 启动后端
cd kb-backend
pip install -r requirements.txt
python main.py
```

### 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OBSIDIAN_VAULT` | *(必须设置)* | Vault 路径 |
| `LLM_PROVIDER` | `auto` | `ollama` / `siliconflow` / `deepseek` / `auto` |
| `OLLAMA_LLM` | `deepseek-r1:7b` | 聊天模型 |
| `OLLAMA_EMBED` | `nomic-embed-text` | 嵌入模型 |
| `SILICONFLOW_KEY` | *(空)* | SiliconFlow 密钥 |
| `DEEPSEEK_KEY` | *(空)* | DeepSeek 官方密钥 |
| `DEEPSEEK_MODEL` | `deepseek-chat` | DeepSeek 模型 |
| `CHUNK_SIZE` | `500` | 文本分块大小 |
| `TOP_K` | `5` | 搜索结果数量 |

### 模型切换

```bash
set LLM_PROVIDER=ollama        # 仅本地
set LLM_PROVIDER=siliconflow   # SiliconFlow 云端
set LLM_PROVIDER=deepseek      # DeepSeek 官方 API
set LLM_PROVIDER=auto          # 自动（Ollama → SF → DeepSeek）
```

| 聊天模型 | 嵌入模型 |
|----------|----------|
| `qwen2.5:3b/7b/14b/32b/72b` | `nomic-embed-text` (768d) |
| `deepseek-r1:1.5b/7b/14b/32b/70b` | `mxbai-embed-large` (1024d) |
| `llama3.1:8b/70b` · `mistral:7b` | `bge-m3` (SiliconFlow) |
| `gemma2:9b` · `phi3:3.8b` · `...` | `gte-qwen2` (SiliconFlow) |

> 所有 Ollama 支持的模型均可使用，设置 `OLLAMA_LLM` 环境变量即可切换。

#### 轻量化推荐（核显 / 无独显 / 低内存）

| 硬件配置 | 推荐模型 | 内存占用 | 说明 |
|----------|----------|----------|------|
| 8GB 内存 | `qwen2.5:3b` | ~2.5GB | 最快，日常问答够用 |
| 8GB 内存 | `deepseek-r1:1.5b` | ~1.5GB | 最小，推理弱但极快 |
| 16GB 内存 | `qwen2.5:7b` | ~5GB | 均衡，推荐首选 |
| 16GB 内存 | `deepseek-r1:7b` | ~5GB | 推理更强 |
| 32GB 内存 | `qwen2.5:14b` | ~9GB | 高质量回答 |
| 32GB 内存 | `deepseek-r1:14b` | ~9GB | 深度推理 |

> 💡 **核显用户：** Ollama 默认 CPU 推理，核显不影响。7b 模型在 16GB 机器上响应约 2-5 秒/句，完全可用。内存不够用 `3b` 或 `1.5b` 即可流畅运行。

### API 概览（30+ 端点）

| 分类 | 端点 |
|------|------|
| 核心 | `/api/chat`, `/api/chat/stream`, `/api/search`, `/api/index` |
| 内容 | `/api/classify`, `/api/links/*` |
| 写作 | `/api/writing/methods`, `/api/writing/results`, `/api/writing/discussion` |
| 知识 | `/api/graph/*`, `/api/conflicts`, `/api/output/*` |
| 系统 | `/api/health`, `/api/status`, `/api/progress/*`, `/api/logs` |

### 自动化功能

| 功能 | 触发条件 | 说明 |
|------|----------|------|
| 增量索引 | 文件创建/修改/删除 | 10s 防抖，自动更新向量库 |
| 内容处理 | 新文件创建 | 自动分类、提取知识点 |
| 冲突检测 | 启动 30s 后 | 扫描概念卡片矛盾 |
| 知识图谱 | 每 6 小时 | 更新概念关联可视化 |
| 失败提取 | 每次问答后 | 从对话中提取失败案例 |
| 对话保存 | 每次问答后 | 保存到 `01_输入区/对话记录/` |

### 目录结构

```
obsagent/
├── kb-plugin/              # Obsidian 插件
│   ├── main.js             # 插件入口
│   ├── api.js              # API 调用
│   ├── styles.css          # 样式
│   └── manifest.json       # 元数据
├── kb-backend/             # 后端服务
│   ├── main.py             # FastAPI 入口（30+ 端点）
│   ├── config.py           # 配置
│   ├── llm.py              # LLM 调用
│   ├── retriever.py        # RAG 检索
│   ├── indexer.py          # 索引管理
│   ├── vectorstore.py      # ChromaDB
│   ├── embeddings.py       # 嵌入模型
│   ├── watcher.py          # 文件监控
│   ├── knowledge_graph.py  # 知识图谱
│   ├── conflict_detector.py# 冲突检测
│   ├── entity_recognizer.py# 实体识别
│   ├── content_classifier.py# 内容分类
│   ├── writing_assistant.py# 写作助手
│   ├── progress_tracker.py # 进度追踪
│   ├── conversation_saver.py# 对话保存
│   ├── failure_tracker.py  # 失败追踪
│   ├── image_processor.py  # 图片处理
│   └── requirements.txt    # Python 依赖
├── docs/                   # GitHub Pages
├── README.md
├── LICENSE                 # Apache 2.0
└── .gitignore
```

## License

[Apache 2.0](LICENSE) — 开源，可自由使用和修改，需保留版权声明。
