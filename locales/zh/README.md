# KB Assistant（知识库助手）

> 基于本地大语言模型的 Obsidian 知识管理全流程插件

[English](../../README.md)

### 功能全景

| 功能 | 说明 |
|------|------|
| **💬 智能问答** | RAG 检索 + 流式输出，自动引用来源 |
| **🔍 混合检索** | 向量语义 + 关键词精确匹配 |
| **🧠 知识图谱** | 从 `[[双向链接]]` 自动构建概念网络 |
| **⚡ 自动索引** | 文件监控 + 增量更新 |
| **📝 引导输入** | 交互式向导创建结构化文档 |
| **📥 快速捕获** | 收件箱模式 |
| **🏷️ 自动分类** | 内容分类 + 标签推荐 |
| **⚠️ 冲突检测** | 发现笔记矛盾 |
| **✍️ 写作助手** | AI 生成方法、结果、讨论 |
| **📈 进度追踪** | 本周统计 + 自动周报 |
| **🖼️ 图片处理** | 图片文字提取 |
| **💾 知识缓存** | 高频问答秒级响应 |

### 快速开始

```bash
# 1. 拉取模型
ollama pull deepseek-r1:7b
ollama pull nomic-embed-text

# 2. 安装插件
cp -r kb-plugin/ <Vault>/.obsidian/plugins/kb-plugin/

# 3. 启动后端
cd kb-backend
pip install -r requirements.txt
set LANG=zh
python main.py
```

### 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `OBSIDIAN_VAULT` | *(必须)* | Vault 路径 |
| `LANG` | `zh` | 语言：`zh` / `en` |
| `LLM_PROVIDER` | `auto` | `ollama` / `siliconflow` / `deepseek` / `auto` |
| `OLLAMA_LLM` | `deepseek-r1:7b` | 聊天模型 |
| `OLLAMA_EMBED` | `nomic-embed-text` | 嵌入模型 |
| `DEEPSEEK_KEY` | *(空)* | DeepSeek 密钥 |
| `GRAPH_SAVE_TO_VAULT` | `false` | 图谱写入vault |

### 轻量化推荐

| 内存 | 模型 | 占用 |
|------|------|------|
| 8GB | `deepseek-r1:1.5b` | ~1.5GB |
| 8GB | `qwen2.5:3b` | ~2.5GB |
| 16GB | `deepseek-r1:7b` | ~5GB |
| 16GB | `qwen2.5:7b` | ~5GB |
| 32GB | `deepseek-r1:14b` | ~9GB |

> 不需要显卡，Ollama 走 CPU 推理。

### 支持模型

| 聊天模型 | 嵌入模型 |
|----------|----------|
| `qwen2.5:3b/7b/14b/32b/72b` | `nomic-embed-text` (768d) |
| `deepseek-r1:1.5b/7b/14b/32b/70b` | `mxbai-embed-large` (1024d) |
| `llama3.1:8b/70b` · `mistral:7b` | `bge-m3` (SiliconFlow) |
| `gemma2:9b` · `phi3:3.8b` · ... | `gte-qwen2` (SiliconFlow) |

> 所有 Ollama 支持的模型均可使用，设置 `OLLAMA_LLM` 环境变量即可切换。

### 大模型适配

| 接入方式 | 配置 | 适合场景 |
|---------|------|---------|
| **Ollama**（默认） | 安装 Ollama，拉取模型 | 隐私、离线、零成本 |
| **DeepSeek** | `set DEEPSEEK_KEY=sk-xxx` | 中文推理最强 |
| **SiliconFlow** | `set SILICONFLOW_KEY=sk-xxx` | 多模型云端 |
| **自动** | `set LLM_PROVIDER=auto` | 回退链：Ollama → SF → DeepSeek |

```bash
# 纯本地（免费、隐私）
set LLM_PROVIDER=ollama
set OLLAMA_LLM=deepseek-r1:7b

# 纯云端（按量付费）
set LLM_PROVIDER=deepseek
set DEEPSEEK_KEY=sk-your-key

# 混合（本地优先，云端兜底）
set LLM_PROVIDER=auto
```

### License

[Apache 2.0](../../LICENSE)
