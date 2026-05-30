import httpx
from typing import List, Dict, Generator, Optional
from config import OLLAMA_BASE, OLLAMA_LLM, SILICONFLOW_API, SILICONFLOW_KEY, SILICONFLOW_LLM_MODEL, LLM_PROVIDER, DEEPSEEK_API, DEEPSEEK_KEY, DEEPSEEK_MODEL
from locale import get_system_prompt

SYSTEM_PROMPT = get_system_prompt()


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


async def chat_deepseek(messages: List[Dict]) -> str:
    if not DEEPSEEK_KEY:
        raise ValueError("DEEPSEEK_KEY 未配置，请设置环境变量 DEEPSEEK_KEY")
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{DEEPSEEK_API}/chat/completions", json={
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "stream": False
        }, headers={"Authorization": f"Bearer {DEEPSEEK_KEY}"})
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def chat(context: str, user_query: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"【知识库内容】\n{context}\n【结束】\n\n用户问题：{user_query}"}
    ]

    if LLM_PROVIDER == "siliconflow":
        return await chat_siliconflow(messages)
    elif LLM_PROVIDER == "deepseek":
        return await chat_deepseek(messages)
    elif LLM_PROVIDER == "ollama":
        return await chat_ollama(messages)
    else:  # auto
        try:
            return await chat_ollama(messages)
        except Exception:
            try:
                return await chat_siliconflow(messages)
            except Exception:
                return await chat_deepseek(messages)


async def chat_stream(context: str, user_query: str) -> Generator[str, None, None]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"【知识库内容】\n{context}\n【结束】\n\n用户问题：{user_query}"}
    ]

    if LLM_PROVIDER == "siliconflow":
        result = await chat_siliconflow(messages)
        yield result
    elif LLM_PROVIDER == "deepseek":
        result = await chat_deepseek(messages)
        yield result
    elif LLM_PROVIDER == "ollama":
        async for chunk in chat_ollama_stream(messages):
            yield chunk
    else:  # auto
        try:
            async for chunk in chat_ollama_stream(messages):
                yield chunk
        except Exception:
            try:
                result = await chat_siliconflow(messages)
                yield result
            except Exception:
                result = await chat_deepseek(messages)
                yield result
