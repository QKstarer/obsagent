import httpx
from typing import List, Dict, Generator, Optional
from config import OLLAMA_BASE, OLLAMA_LLM, SILICONFLOW_API, SILICONFLOW_KEY, SILICONFLOW_LLM_MODEL

SYSTEM_PROMPT = """你是一个基于知识库的智能助手，专注于基因编辑和表观遗传学研究。你的唯一知识来源是下方提供的【知识库内容】。

核心规则：
1. 你必须严格基于【知识库内容】来回答问题，不要使用你自己的知识
2. 如果知识库中有相关内容，必须引用来源，格式：[来源: 文件名]
3. 如果知识库中没有相关内容，直接说"知识库中未找到相关信息"
4. 回答使用中文
5. 不要编造或推测知识库中没有的信息

专业术语规范：
- 基因名称：斜体小写（如 *dnmt3a*、*tet2*），人类基因全大写（如 DNMT3A）
- 蛋白名称：正体首字母大写（如 DNMT3A、TET2），结构域全大写（如 KRAB、DNMT3L）
- CRISPR 系统：首字母大写（如 CRISPRoff、CRISPRi、dCas9）
- 测序方法：大写缩写（如 BSP测序、WGBS、ChIP-seq）
- 表观遗传标记：标准写法（如 5mC、H3K4me3、H3K27me3）

回答风格：
- 简洁准确，避免冗余
- 使用结构化格式（标题、列表、表格）
- 如有相关概念，使用 [[双向链接]] 格式引用"""


async def chat_ollama(messages: List[Dict]) -> str:
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{OLLAMA_BASE}/api/chat", json={
            "model": OLLAMA_LLM,
            "messages": messages,
            "stream": False
        })
        resp.raise_for_status()
        return resp.json()["message"]["content"]


async def chat_ollama_stream(messages: List[Dict]) -> Generator[str, None, None]:
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{OLLAMA_BASE}/api/chat", json={
            "model": OLLAMA_LLM,
            "messages": messages,
            "stream": True
        }) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    import json
                    try:
                        data = json.loads(line)
                        if "message" in data:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue


async def chat_siliconflow(messages: List[Dict]) -> str:
    if not SILICONFLOW_KEY:
        raise ValueError("SILICONFLOW_KEY 未配置，请设置环境变量 SILICONFLOW_KEY")
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{SILICONFLOW_API}/chat/completions", json={
            "model": SILICONFLOW_LLM_MODEL,
            "messages": messages,
            "stream": False
        }, headers={"Authorization": f"Bearer {SILICONFLOW_KEY}"})
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def chat(context: str, user_query: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"【知识库内容】\n{context}\n【结束】\n\n用户问题：{user_query}"}
    ]
    try:
        return await chat_ollama(messages)
    except Exception:
        return await chat_siliconflow(messages)


async def chat_stream(context: str, user_query: str) -> Generator[str, None, None]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"【知识库内容】\n{context}\n【结束】\n\n用户问题：{user_query}"}
    ]
    try:
        async for chunk in chat_ollama_stream(messages):
            yield chunk
    except Exception:
        result = await chat_siliconflow(messages)
        yield result
