# KB Assistant (知识库助手)

> 基于本地大语言模型的 Obsidian 知识库智能问答插件

[![Obsidian](https://img.shields.io/badge/Obsidian-%E2%89%A5%201.0.0-7C3AED?logo=obsidian)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-%E2%89%A5%203.9-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

[English](#english) | [中文](#中文)

---

## English

### Features

- **Smart Q&A**: RAG-based answers with source citations, no hallucination
- **Hybrid Search**: Vector semantic + keyword exact matching, dual-engine fusion
- **Auto Indexing**: Watch file changes, auto-update vector database
- **Model Switching**: Ollama local + SiliconFlow cloud, one env var to switch
- **Conflict Detection**: Auto-detect contradictions between concept cards
- **Knowledge Graph**: Visualize concept relationships
- **Quick Capture**: Inbox mode for quickly recording ideas
- **Security**: CORS origin restriction, UTF-8/GBK encoding support, health check

### Architecture

```
┌─────────────────────────┐      HTTP       ┌─────────────────────────┐
│   Obsidian Plugin        │ ◄─────────────► │   Python Backend         │
│   (TypeScript)           │                 │   (FastAPI + RAG)        │
│                          │                 │                          │
│  · Chat UI + Streaming   │  POST /api/     │  · Retriever (Vector+KW) │
│  · Sidebar Panel         │     chat        │  · ChromaDB              │
│  · Command Palette       │ ──────────────  │  · Ollama / SiliconFlow  │
└─────────────────────────┘                 └─────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | TypeScript + Obsidian API |
| Backend | Python + FastAPI |
| Vector DB | ChromaDB |
| Embeddings | nomic-embed-text (Ollama) / bge-m3 (SiliconFlow) |
| LLM | qwen2.5:7b (Ollama) / DeepSeek-R1 (SiliconFlow) |

### Quick Start

**Prerequisites:**
- Obsidian ≥ 1.0.0
- Python ≥ 3.9
- [Ollama](https://ollama.ai) installed and running

**1. Pull models:**
```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

**2. Install plugin:**
Copy `kb-plugin/` to your vault:
```
<Vault>/.obsidian/plugins/kb-plugin/
```
Then enable "知识库助手" in Obsidian → Settings → Community plugins.

**3. Start backend:**
```bash
cd kb-backend
pip install -r requirements.txt
python main.py
```

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OBSIDIAN_VAULT` | *(must set)* | Vault path |
| `LLM_PROVIDER` | `auto` | `ollama` / `siliconflow` / `auto` |
| `OLLAMA_BASE` | `http://localhost:11434` | Ollama address |
| `OLLAMA_LLM` | `qwen2.5:7b` | Chat model |
| `OLLAMA_EMBED` | `nomic-embed-text` | Embedding model |
| `SILICONFLOW_API` | `https://api.siliconflow.cn/v1` | SiliconFlow API |
| `SILICONFLOW_KEY` | *(empty)* | SiliconFlow API key |
| `SILICONFLOW_LLM_MODEL` | `deepseek-ai/DeepSeek-R1` | Cloud chat model |
| `SILICONFLOW_EMBED_MODEL` | `BAAI/bge-m3` | Cloud embedding model |
| `CHUNK_SIZE` | `500` | Text chunk size |
| `TOP_K` | `5` | Search results count |

### Supported Models

| Model | Type | Best For |
|-------|------|----------|
| `qwen2.5:3b` | Chat | Fastest, low-end machines |
| `qwen2.5:7b` | Chat | Balanced, default |
| `qwen2.5:14b` | Chat | Best quality, 16GB+ RAM |
| `deepseek-r1:7b` | Chat | Strong reasoning |
| `nomic-embed-text` | Embed | Lightweight, 768d |
| `mxbai-embed-large` | Embed | Higher accuracy, 1024d |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/chat` | Smart Q&A |
| POST | `/api/chat/stream` | Streaming Q&A |
| GET | `/api/search` | Vector search |
| POST | `/api/index` | Re-index vault |
| GET | `/api/status` | System status |
| GET | `/api/conflicts` | Concept conflicts |
| POST | `/api/links` | Related links |
| POST | `/api/inbox` | Quick capture |

---

## 中文

### 功能特性

- **智能问答**：基于 RAG 技术，严格依据知识库内容回答，自动引用来源，杜绝幻觉
- **混合检索**：向量语义搜索 + 关键词精确匹配，双引擎融合
- **自动索引**：监控文件变更，自动更新向量数据库
- **模型切换**：Ollama 本地 + SiliconFlow 云端，环境变量一键切换
- **冲突检测**：自动检测概念卡片之间的矛盾
- **知识图谱**：可视化概念关联关系
- **快速捕获**：收件箱模式，快速记录灵感
- **安全加固**：CORS 来源限制、输入编码兼容、健康检查端点

### 技术栈

| 组件 | 技术 |
|------|------|
| 前端插件 | TypeScript + Obsidian API |
| 后端服务 | Python + FastAPI |
| 向量数据库 | ChromaDB |
| 嵌入模型 | nomic-embed-text (Ollama) / bge-m3 (SiliconFlow) |
| 大语言模型 | qwen2.5:7b (Ollama) / DeepSeek-R1 (SiliconFlow) |

### 快速开始

**前置条件：**
- Obsidian ≥ 1.0.0
- Python ≥ 3.9
- [Ollama](https://ollama.ai) 已安装并运行

**1. 拉取模型：**
```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

**2. 安装插件：**
将 `kb-plugin/` 复制到你的 vault：
```
<Vault>/.obsidian/plugins/kb-plugin/
```
然后在 Obsidian → 设置 → 第三方插件中启用"知识库助手"。

**3. 启动后端：**
```bash
cd kb-backend
pip install -r requirements.txt
python main.py
```

### 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OBSIDIAN_VAULT` | *(必须设置)* | Vault 路径 |
| `LLM_PROVIDER` | `auto` | `ollama` / `siliconflow` / `auto` |
| `OLLAMA_BASE` | `http://localhost:11434` | Ollama 地址 |
| `OLLAMA_LLM` | `qwen2.5:7b` | 聊天模型 |
| `OLLAMA_EMBED` | `nomic-embed-text` | 嵌入模型 |
| `SILICONFLOW_API` | `https://api.siliconflow.cn/v1` | SiliconFlow API |
| `SILICONFLOW_KEY` | *(空)* | SiliconFlow 密钥 |
| `SILICONFLOW_LLM_MODEL` | `deepseek-ai/DeepSeek-R1` | 云端聊天模型 |
| `SILICONFLOW_EMBED_MODEL` | `BAAI/bge-m3` | 云端嵌入模型 |
| `CHUNK_SIZE` | `500` | 文本分块大小 |
| `TOP_K` | `5` | 搜索结果数量 |

### 模型切换

```bash
# 仅用本地 Ollama
set LLM_PROVIDER=ollama

# 仅用云端 SiliconFlow
set LLM_PROVIDER=siliconflow
set SILICONFLOW_KEY=你的密钥

# 自动模式（优先本地，失败回云端）
set LLM_PROVIDER=auto
```

### 支持模型

| 模型 | 类型 | 特点 |
|------|------|------|
| `qwen2.5:3b` | 聊天 | 最快，低配机器 |
| `qwen2.5:7b` | 聊天 | 均衡，**默认推荐** |
| `qwen2.5:14b` | 聊天 | 更强，需 16GB+ 内存 |
| `deepseek-r1:7b` | 聊天 | 推理能力强 |
| `nomic-embed-text` | 嵌入 | 轻量，768维 |
| `mxbai-embed-large` | 嵌入 | 更精确，1024维 |

### 目录结构

```
obsagent/
├── kb-plugin/              # Obsidian 插件（TypeScript）
│   ├── main.js             # 插件入口
│   ├── api.js              # 后端 API 调用
│   ├── styles.css          # 样式
│   └── manifest.json       # 插件元数据
├── kb-backend/             # 后端服务（Python）
│   ├── main.py             # FastAPI 入口 + 健康检查
│   ├── config.py           # 配置（全部环境变量可覆盖）
│   ├── llm.py              # LLM 调用（Ollama/SiliconFlow）
│   ├── retriever.py        # RAG 检索（向量+关键词）
│   ├── indexer.py          # 索引管理
│   ├── vectorstore.py      # ChromaDB 封装
│   ├── embeddings.py       # 嵌入模型（并行批处理）
│   ├── watcher.py          # 文件监控（增量更新）
│   └── requirements.txt    # Python 依赖
├── docs/                   # GitHub Pages
│   └── index.html          # 项目主页
├── README.md
├── LICENSE                 # Apache 2.0
├── install.bat             # Windows 一键安装
└── start-backend.bat       # Windows 一键启动
```

## License

[Apache 2.0](LICENSE) — 开源，可自由使用和修改，需保留版权声明。
