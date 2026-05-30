# KB Assistant（知识库助手）

> 基于本地大语言模型的 Obsidian 知识管理全流程插件

[![Obsidian](https://img.shields.io/badge/Obsidian-%E2%89%A5%201.0.0-7C3AED?logo=obsidian)](https://obsidian.md)
[![Python](https://img.shields.io/badge/Python-%E2%89%A5%203.9-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**[English](README.md)**

### 功能介绍

KB Assistant 不只是问答工具——它自动组织、处理、连接你的知识，让大模型通过知识库持续学习。

### 功能全景

| 功能 | 说明 |
|------|------|
| **💬 智能问答** | RAG 检索 + 流式输出，自动引用来源和概念链接 |
| **🔍 混合检索** | 向量语义 + 关键词精确匹配，双引擎融合 |
| **🧠 知识图谱** | 从 `[[双向链接]]` 自动构建概念关系网络 |
| **⚡ 自动索引** | 文件监控 + 增量更新，修改即生效 |
| **📝 引导输入** | 交互式向导，按模板创建结构化文档 |
| **📥 快速捕获** | 收件箱模式，随时记录灵感 |
| **🏷️ 自动分类** | 内容分类 + 标签推荐 |
| **⚠️ 冲突检测** | 发现笔记间的矛盾信息 |
| **✍️ 写作助手** | AI 生成方法、结果、讨论章节 |
| **📈 进度追踪** | 本周工作统计 + 自动周报 |
| **🖼️ 图片处理** | 图片文字提取，自动转为笔记 |
| **💾 知识缓存** | 高频问答自动缓存，秒级响应 |

### 系统架构

```
┌───────────────────────────────────────────────────┐
│                  Obsidian 插件                      │
│  聊天界面 · 引导输入 · 收件箱 · 命令面板             │
└──────────────────────┬────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼────────────────────────────┐
│                  Python 后端                        │
│                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ RAG      │ │ 知识图谱  │ │ 缓存层   │           │
│  │ 检索器   │ │ 增强检索  │ │          │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 内容处理  │ │ 写作助手  │ │ 冲突检测  │           │
│  └──────────┘ └──────────┘ └──────────┘           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ 文件监控  │ │ ChromaDB │ │ Ollama / │           │
│  │          │ │ 向量数据库│ │ DeepSeek │           │
│  └──────────┘ └──────────┘ └──────────┘           │
└───────────────────────────────────────────────────┘
```

### 检索流程

```
查询 → ① 缓存命中? → 秒级返回
       ↓ 未命中
       ② 向量检索 + 关键词检索
       ③ 知识图谱提取关联概念
       ④ 合并上下文 → LLM 生成回答
       ⑤ 缓存答案供下次使用
```

### 技术栈

| 组件 | 技术 |
|------|------|
| 前端插件 | TypeScript + Obsidian API |
| 后端服务 | Python + FastAPI |
| 向量数据库 | ChromaDB |
| 嵌入模型 | nomic-embed-text / bge-m3 |
| 大语言模型 | deepseek-r1（Ollama 本地 / DeepSeek API） |
| 知识图谱 | 从 `[[双向链接]]` 自动构建 |
| 缓存 | JSON + LRU 清理 |

### 快速开始

**前置条件：** Obsidian ≥ 1.0.0, Python ≥ 3.9, [Ollama](https://ollama.ai)

```bash
# 1. 拉取模型
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text

# 2. 安装插件
cp -r kb-plugin/ <Vault>/.obsidian/plugins/kb-plugin/

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
| `DEEPSEEK_KEY` | *(空)* | DeepSeek 官方密钥 |
| `SILICONFLOW_KEY` | *(空)* | SiliconFlow 密钥 |
| `CHUNK_SIZE` | `500` | 文本分块大小 |
| `TOP_K` | `5` | 搜索结果数量 |

### 支持模型

| 聊天模型 | 嵌入模型 |
|----------|----------|
| `qwen2.5:3b/7b/14b/32b/72b` | `nomic-embed-text` (768d) |
| `deepseek-r1:1.5b/7b/14b/32b/70b` | `mxbai-embed-large` (1024d) |
| `llama3.1:8b/70b` · `mistral:7b` | `bge-m3` (SiliconFlow) |
| `gemma2:9b` · `phi3:3.8b` · ... | `gte-qwen2` (SiliconFlow) |

> 所有 Ollama 支持的模型均可使用，设置 `OLLAMA_LLM` 环境变量即可切换。

#### 轻量化推荐（核显 / 无独显 / 低内存）

| 硬件配置 | 推荐模型 | 内存占用 | 说明 |
|----------|----------|----------|------|
| 8GB | `deepseek-r1:1.5b` | ~1.5GB | 最小，最快 |
| 8GB | `qwen2.5:3b` | ~2.5GB | 日常问答 |
| 16GB | `deepseek-r1:7b` | ~5GB | **推荐首选** |
| 16GB | `qwen2.5:7b` | ~5GB | 均衡 |
| 32GB | `deepseek-r1:14b` | ~9GB | 深度推理 |
| 32GB | `qwen2.5:14b` | ~9GB | 高质量 |

> 💡 **核显用户：** Ollama 默认 CPU 推理，不需要显卡。7b 模型在 16GB 机器上响应约 2-5 秒。

### API 端点（30+）

| 分类 | 端点 |
|------|------|
| 核心 | `/api/chat`, `/api/chat/stream`, `/api/search`, `/api/index` |
| 知识图谱 | `/api/kg`, `/api/kg/related`, `/api/graph/*` |
| 缓存 | `/api/cache`, `/api/cache/clear` |
| 内容 | `/api/classify`, `/api/links/*` |
| 写作 | `/api/writing/methods`, `/api/writing/results`, `/api/writing/discussion` |
| 系统 | `/api/health`, `/api/status`, `/api/progress/*`, `/api/logs` |

### 自动化功能

| 功能 | 触发条件 | 说明 |
|------|----------|------|
| 增量索引 | 文件变更 | 10s 防抖，自动更新向量库 |
| 知识图谱 | 每 5 分钟 | 自动重建概念关系网络 |
| 知识缓存 | 每次查询 | 高频问答自动缓存 |
| 冲突检测 | 启动时 | 扫描笔记矛盾 |
| 进度报告 | 每周 | 统计与自动周报 |

### 项目结构

```
obsagent/
├── kb-plugin/                # Obsidian 插件
│   ├── main.js
│   ├── api.js
│   ├── styles.css
│   └── manifest.json
├── kb-backend/               # Python 后端
│   ├── main.py               # FastAPI 入口（30+ 端点）
│   ├── config.py             # 配置
│   ├── llm.py                # LLM 调用（Ollama/SF/DeepSeek）
│   ├── retriever.py          # RAG + 知识图谱 + 缓存检索
│   ├── kg_retriever.py       # 知识图谱增强检索
│   ├── knowledge_cache.py    # 问答缓存
│   ├── vectorstore.py        # ChromaDB
│   ├── embeddings.py         # 嵌入模型
│   ├── indexer.py            # 索引管理
│   ├── watcher.py            # 文件监控
│   ├── knowledge_graph.py    # 图谱生成
│   ├── conflict_detector.py  # 冲突检测
│   ├── content_classifier.py # 自动分类
│   ├── writing_assistant.py  # 写作助手
│   ├── progress_tracker.py   # 进度追踪
│   ├── conversation_saver.py # 对话保存
│   ├── failure_tracker.py    # 失败提取
│   ├── image_processor.py    # 图片处理
│   └── requirements.txt
├── docs/                     # GitHub Pages
├── README.md                 # English
├── README_CN.md              # 中文文档
├── LICENSE                   # Apache 2.0
└── .gitignore
```

## License

[Apache 2.0](LICENSE) — 开源，可自由使用和修改，需保留版权声明。
