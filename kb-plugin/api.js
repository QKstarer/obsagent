"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.setApiBase = setApiBase;
exports.getApiBase = getApiBase;
exports.chatWithKB = chatWithKB;
exports.chatWithKBStream = chatWithKBStream;
exports.searchKB = searchKB;
exports.rebuildIndex = rebuildIndex;
exports.getStatus = getStatus;
exports.getProgress = getProgress;
exports.getConflicts = getConflicts;
exports.getFailures = getFailures;
exports.getLogs = getLogs;
exports.getSgRNA = getSgRNA;
exports.getBSP = getBSP;
exports.getWriting = getWriting;
exports.processImage = processImage;
exports.getGraph = getGraph;
let API_BASE = "http://localhost:8000";
function setApiBase(base) {
    API_BASE = base;
}
function getApiBase() {
    return API_BASE;
}
async function chatWithKB(query) {
    const resp = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
    });
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function chatWithKBStream(query, onChunk, onSources) {
    const resp = await fetch(`${API_BASE}/api/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
    });
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    const reader = resp.body?.getReader();
    if (!reader)
        return;
    const decoder = new TextDecoder();
    while (true) {
        const { done, value } = await reader.read();
        if (done)
            break;
        const text = decoder.decode(value);
        const lines = text.split("\n");
        for (const line of lines) {
            if (line.startsWith("data: ")) {
                const data = line.slice(6);
                if (data === "[DONE]")
                    return;
                try {
                    const parsed = JSON.parse(data);
                    if (parsed.content)
                        onChunk(parsed.content);
                    if (parsed.sources)
                        onSources(parsed.sources);
                }
                catch { }
            }
        }
    }
}
async function searchKB(query, topK = 5) {
    const resp = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}&top_k=${topK}`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    const data = await resp.json();
    return data.results;
}
async function rebuildIndex() {
    const resp = await fetch(`${API_BASE}/api/index`, { method: "POST" });
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getStatus() {
    const resp = await fetch(`${API_BASE}/api/status`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getProgress() {
    const resp = await fetch(`${API_BASE}/api/progress`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getConflicts() {
    const resp = await fetch(`${API_BASE}/api/conflicts`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getFailures() {
    const resp = await fetch(`${API_BASE}/api/failures`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getLogs(count = 20) {
    const resp = await fetch(`${API_BASE}/api/logs?count=${count}`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getSgRNA(gene) {
    const url = gene ? `${API_BASE}/api/sgrna?gene=${gene}` : `${API_BASE}/api/sgrna`;
    const resp = await fetch(url);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getBSP() {
    const resp = await fetch(`${API_BASE}/api/bsp`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getWriting() {
    const resp = await fetch(`${API_BASE}/api/writing`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function processImage(filename, base64Data) {
    const resp = await fetch(`${API_BASE}/api/image/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, data: base64Data }),
    });
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
async function getGraph() {
    const resp = await fetch(`${API_BASE}/api/graph`);
    if (!resp.ok)
        throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
