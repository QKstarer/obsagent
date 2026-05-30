# KB Assistant (知识库助手)

> 基于本地大语言模型的 Obsidian 知识库智能问答插件

[![Obsidian](https://img.shields.io/badge/Obsidian-%E2%89%A5%201.0.0-7C3AED?logo=obsidian)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-%E2%89%A5%203.9-3776AB?logo=python)](https://python.org)

[English](#english) | [中文](#中文)

---

## English

### Features

- **Smart Q&A**: Answer questions based on your knowledge base content with source citations
- **Vector Search**: ChromaDB + nomic-embed-text for semantic search
- **Auto Indexing**: Watch file changes and automatically update vector database
- **Content Processing**: Auto-classification, entity recognition, link suggestions
- **Structured Input**: Guided creation of experiment records, literature notes, etc.
- **Quick Capture**: Inbox mode for quickly recording ideas
- **Conflict Detection**: Auto-detect contradictions between concept cards
- **Knowledge Graph**: Visualize concept relationships

### Architecture

```
┌─────────────────────┐     HTTP      ┌─────────────────────┐
│   Obsidian Plugin    │ ◄──────────► │   Python Backend     │
│   (TypeScript)       │              │   (FastAPI)          │
│                      │              │                      │
│  · Chat UI           │              │  · RAG Pipeline      │
│  · Sidebar Panel     │              │  · ChromaDB          │
│  · Command Palette   │              │  · Ollama (LLM+Emb)  │
└─────────────────────┘              └─────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | TypeScript + Obsidian API |
| Backend | Python + FastAPI |
| Vector DB | ChromaDB |
| Embeddings | nomic-embed-text (Ollama) |
| LLM | qwen2.5:7b (Ollama) |

### Quick Start

**Prerequisites:**
- Obsidian ≥ 1.0.0
- Python ≥ 3.9
- [Ollama](https://ollama.ai) installed and running

**1. Pull models:**
```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
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
| `OBSIDIAN_VAULT` | Auto-detect | Vault path |
| `OLLAMA_BASE` | `http://localhost:11434` | Ollama address |
| `OLLAMA_LLM` | `qwen2.5:7b` | Chat model |
| `OLLAMA_EMBED` | `nomic-embed-text` | Embedding model |
| `SILICONFLOW_API` | - | SiliconFlow API (alternative) |
| `SILICONFLOW_KEY` | - | SiliconFlow API key |

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Smart Q&A |
| POST | `/api/index` | Re-index vault |
| GET | `/api/status` | System status |
| GET | `/api/progress` | Weekly progress |
| POST | `/api/conflicts` | Detect concept conflicts |
| POST | `/api/links` | Recommend related links |
| POST | `/api/inbox` | Quick capture |

---

## 中文

### 功能特性

- **智能问答**：基于知识库内容回答问题，自动引用来源
- **知识检索**：向量搜索 + 关键词搜索，精准定位内容
- **自动索引**：监控文件变更，自动更新向量数据库
- **内容处理**：自动分类、实体识别、链接推荐
- **结构化输入**：引导式创建实验记录、文献笔记等
- **快速捕获**：收件箱模式，快速记录灵感
- **冲突检测**：自动检测概念卡片之间的矛盾
- **知识图谱**：可视化概念关联关系

### 技术栈

| 组件 | 技术 |
|------|------|
| 前端插件 | TypeScript + Obsidian API |
| 后端服务 | Python + FastAPI |
| 向量数据库 | ChromaDB |
| 嵌入模型 | nomic-embed-text (Ollama) |
| 大语言模型 | qwen2.5:7b (Ollama) |

### 快速开始

**前置条件：**
- Obsidian ≥ 1.0.0
- Python ≥ 3.9
- [Ollama](https://ollama.ai) 已安装并运行

**1. 拉取模型：**
```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
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
| `OBSIDIAN_VAULT` | 自动检测 | Vault 路径 |
| `OLLAMA_BASE` | `http://localhost:11434` | Ollama 地址 |
| `OLLAMA_LLM` | `qwen2.5:7b` | 聊天模型 |
| `OLLAMA_EMBED` | `nomic-embed-text` | 嵌入模型 |
| `SILICONFLOW_API` | - | SiliconFlow API（备选） |
| `SILICONFLOW_KEY` | - | SiliconFlow 密钥 |

### 目录结构

```
obsagent/
├── kb-plugin/              # Obsidian 插件（TypeScript）
│   ├── main.js             # 插件入口
│   ├── api.js              # 后端 API 调用
│   ├── styles.css          # 样式
│   └── manifest.json       # 插件元数据
├── kb-backend/             # 后端服务（Python）
│   ├── main.py             # FastAPI 入口
│   ├── config.py           # 配置
│   ├── retriever.py        # RAG 检索
│   ├── indexer.py          # 索引管理
│   ├── vectorstore.py      # ChromaDB 封装
│   ├── llm.py              # LLM 调用
│   ├── embeddings.py       # 嵌入模型
│   ├── watcher.py          # 文件监控
│   ├── knowledge_graph.py  # 知识图谱
│   ├── conflict_detector.py# 冲突检测
│   └── requirements.txt    # Python 依赖
├── README.md
├── install.bat             # Windows 一键安装
└── start-backend.bat       # Windows 一键启动
```

## License

[Apache 2.0](LICENSE) — 开源，可自由使用和修改，需保留版权声明。
