"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const obsidian_1 = require("obsidian");
const api_1 = require("./api");
const DEFAULT_SETTINGS = {
    backendPort: 8000,
    backendPath: "",
    autoStart: true,
};
const VIEW_TYPE_KB_CHAT = "kb-chat-view";
class ChatView extends obsidian_1.ItemView {
    constructor(leaf) {
        super(leaf);
        this.inputMode = "normal";
        this.guidedStep = 0;
        this.guidedData = {};
    }
    getViewType() { return VIEW_TYPE_KB_CHAT; }
    getDisplayText() { return "知识库助手"; }
    getIcon() { return "bot"; }
    async onOpen() {
        const container = this.containerEl.children[1];
        if (!container)
            return;
        container.empty();
        container.addClass("kb-chat-container");
        // Status bar
        this.statusEl = container.createDiv({ cls: "kb-status-bar" });
        this.updateStatus();
        // Toolbar
        const toolbar = container.createDiv({ cls: "kb-chat-toolbar" });
        const statusBtn = toolbar.createEl("button", { text: "状态", cls: "kb-toolbar-btn" });
        statusBtn.onclick = () => this.showStatus();
        const progressBtn = toolbar.createEl("button", { text: "进度", cls: "kb-toolbar-btn" });
        progressBtn.onclick = () => this.showProgress();
        const conflictBtn = toolbar.createEl("button", { text: "冲突", cls: "kb-toolbar-btn" });
        conflictBtn.onclick = () => this.showConflicts();
        const historyBtn = toolbar.createEl("button", { text: "历史", cls: "kb-toolbar-btn" });
        historyBtn.onclick = () => this.showHistory();
        const guideBtn = toolbar.createEl("button", { text: "引导输入", cls: "kb-toolbar-btn" });
        guideBtn.onclick = () => this.startGuidedInput();
        const inboxBtn = toolbar.createEl("button", { text: "收件箱", cls: "kb-toolbar-btn" });
        inboxBtn.onclick = () => this.openInbox();
        // Messages
        this.messagesEl = container.createDiv({ cls: "kb-chat-messages" });
        this.loadingEl = container.createDiv({ cls: "kb-loading" });
        this.loadingEl.style.display = "none";
        this.showEmptyState();
        // Input
        const inputArea = container.createDiv({ cls: "kb-chat-input-area" });
        this.inputEl = inputArea.createEl("textarea", {
            cls: "kb-chat-input",
            placeholder: "输入问题... (Enter 发送，Shift+Enter 换行)",
        });
        this.inputEl.rows = 2;
        const sendBtn = inputArea.createEl("button", { text: "发送", cls: "kb-chat-send" });
        const send = () => {
            const q = this.inputEl.value.trim();
            if (!q)
                return;
            this.inputEl.value = "";
            this.sendMessage(q);
        };
        sendBtn.onclick = send;
        this.inputEl.onkeydown = (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
            }
        };
        // Quick actions
        const quickActions = container.createDiv({ cls: "kb-quick-actions" });
        quickActions.createEl("span", { text: "快捷问题:", cls: "kb-quick-label" });
        const questions = [
            "CRISPRoff是什么？",
            "如何设计sgRNA？",
            "BSP测序的原理？",
            "DNA甲基化的作用？",
        ];
        for (const q of questions) {
            const btn = quickActions.createEl("button", { text: q, cls: "kb-quick-btn" });
            btn.onclick = () => this.sendMessage(q);
        }
    }
    async uploadImage() {
        this.addSystemMessage(`⚠️ 图片识别功能暂未开放`);
    }
    async updateStatus() {
        try {
            const s = await (0, api_1.getStatus)();
            const conversations = s.conversations;
            this.statusEl.setText(`向量: ${s.total_chunks} | 对话: ${conversations?.total || 0}`);
        }
        catch {
            this.statusEl.setText("后端未连接");
        }
    }
    async showStatus() {
        try {
            const s = await (0, api_1.getStatus)();
            const conversations = s.conversations;
            this.addSystemMessage(`📊 系统状态\n` +
                `• 状态: ${s.status}\n` +
                `• 向量数: ${s.total_chunks}\n` +
                `• 对话数: ${conversations?.total || 0}\n` +
                `• 今日对话: ${conversations?.today || 0}`);
        }
        catch {
            this.addSystemMessage("后端未连接，请先启动 kb-backend");
        }
    }
    async showProgress() {
        try {
            const p = await (0, api_1.getProgress)();
            let msg = `📈 本周进度\n• 更新文件: ${p.total_updates} 个\n`;
            for (const [cat, count] of Object.entries(p.categories || {})) {
                msg += `• ${cat}: ${count} 个\n`;
            }
            this.addSystemMessage(msg);
        }
        catch {
            this.addSystemMessage("获取进度失败");
        }
    }
    async showConflicts() {
        try {
            const c = await (0, api_1.getConflicts)();
            if (c.status === "scanning") {
                this.addSystemMessage("冲突扫描进行中...");
            }
            else if (c.total_conflicts === 0) {
                this.addSystemMessage("✅ 未发现冲突");
            }
            else {
                this.addSystemMessage(`⚠️ 发现 ${c.total_conflicts} 个冲突`);
            }
        }
        catch {
            this.addSystemMessage("获取冲突信息失败");
        }
    }
    showEmptyState() {
        this.messagesEl.createDiv({
            cls: "kb-empty-state",
            text: "基于你的 Obsidian 知识库进行问答\n\n请先启动 kb-backend 后端服务\n\n快捷问题：点击下方按钮快速提问",
        });
    }
    clearEmptyState() {
        const empty = this.messagesEl.querySelector(".kb-empty-state");
        if (empty)
            empty.remove();
    }
    addUserMessage(text) {
        this.clearEmptyState();
        const msg = this.messagesEl.createDiv({ cls: "kb-message kb-message-user" });
        msg.createEl("span", { text });
        this.scrollToBottom();
    }
    createAIMessage() {
        return this.messagesEl.createDiv({ cls: "kb-message kb-message-ai" });
    }
    addSystemMessage(text) {
        const msg = this.messagesEl.createDiv({ cls: "kb-message kb-message-system" });
        msg.createEl("pre", { text });
        this.scrollToBottom();
    }
    scrollToBottom() {
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }
    showLoading(show) {
        this.loadingEl.style.display = show ? "block" : "none";
        this.loadingEl.setText(show ? "正在处理..." : "");
    }
    renderSources(container, sources) {
        if (!sources.length)
            return;
        const srcDiv = container.createDiv({ cls: "kb-sources" });
        srcDiv.createEl("div", { text: "来源:", cls: "kb-source-score" });
        for (const s of sources) {
            const item = srcDiv.createDiv({ cls: "kb-source-item" });
            const title = s.title || s.source.split("/").pop() || s.source;
            item.createSpan({ text: title });
            item.createSpan({ text: `${(s.score * 100).toFixed(0)}%`, cls: "kb-source-score" });
            item.onclick = async () => {
                const file = this.app.vault.getAbstractFileByPath(s.source);
                if (file) {
                    await this.app.workspace.getLeaf().openFile(file);
                }
            };
        }
    }
    async sendMessage(query) {
        // Check if in guided input mode
        if (this.inputMode === "guided") {
            this.addUserMessage(query);
            const handled = await this.handleGuidedInput(query);
            if (handled)
                return;
        }
        this.addUserMessage(query);
        this.addToHistory(query);
        this.showLoading(true);
        const aiMsg = this.createAIMessage();
        let fullText = "";
        try {
            await (0, api_1.chatWithKBStream)(query, (chunk) => {
                fullText += chunk;
                aiMsg.innerHTML = "";
                const p = aiMsg.createEl("p");
                p.setText(fullText);
                this.scrollToBottom();
            }, (sources) => {
                this.renderSources(aiMsg, sources);
                // Show related concepts graph
                this.showRelatedGraph(query, aiMsg);
            });
        }
        catch (err) {
            aiMsg.createEl("p", { text: `错误: ${err}` });
        }
        finally {
            this.showLoading(false);
            this.scrollToBottom();
            this.updateStatus();
        }
    }
    async showRelatedGraph(query, container) {
        try {
            // @ts-ignore
            const response = await fetch(`${(0, api_1.getApiBase)()}/api/entities/recognize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: query }),
            });
            const data = await response.json();
            if (data.links && data.links.length > 0) {
                const graphDiv = container.createDiv({ cls: "kb-related-graph" });
                graphDiv.createEl("div", { text: "🔗 相关概念:", cls: "kb-graph-title" });
                const linksDiv = graphDiv.createDiv({ cls: "kb-graph-links" });
                for (const link of data.links.slice(0, 5)) {
                    const linkEl = linksDiv.createEl("span", { text: link, cls: "kb-graph-link" });
                    linkEl.onclick = async () => {
                        // @ts-ignore
                        const file = this.app.vault.getAbstractFileByPath(`02_知识加工区/概念卡片/${link.replace(/\[\[|\]\]/g, "")}.md`);
                        if (file) {
                            // @ts-ignore
                            await this.app.workspace.getLeaf().openFile(file);
                        }
                    };
                }
            }
        }
        catch (err) {
            console.error("Failed to show related graph:", err);
        }
    }
    addToHistory(query) {
        const history = JSON.parse(localStorage.getItem("kb-search-history") || "[]");
        history.unshift({ query, time: new Date().toISOString() });
        if (history.length > 50)
            history.pop();
        localStorage.setItem("kb-search-history", JSON.stringify(history));
    }
    getHistory() {
        return JSON.parse(localStorage.getItem("kb-search-history") || "[]");
    }
    showHistory() {
        const history = this.getHistory();
        if (history.length === 0) {
            this.addSystemMessage("📝 暂无搜索历史");
            return;
        }
        let msg = "📝 搜索历史（最近20条）\n\n";
        history.slice(0, 20).forEach((h, i) => {
            const time = new Date(h.time).toLocaleString("zh-CN");
            msg += `${i + 1}. ${h.query}  (${time})\n`;
        });
        this.addSystemMessage(msg);
    }
    startGuidedInput() {
        this.clearEmptyState();
        const msg = this.messagesEl.createDiv({ cls: "kb-message kb-message-system" });
        msg.createEl("pre", { text: `📝 正式文档 - 结构化输入

这里是创建正式文档的入口，按标准格式整理内容。

📋 支持的文档类型：

1️⃣ 实验记录 - 标准实验报告格式
   包含：目的、方法、结果、分析

2️⃣ 文献笔记 - 文献整理格式
   包含：摘要、创新点、方法、启示

3️⃣ 概念卡片 - 知识点整理格式
   包含：定义、机制、应用、关联

4️⃣ 实验方案 - 实验设计格式
   包含：目的、材料、步骤、预期

5️⃣ 问题案例 - 问题解决格式
   包含：问题、原因、方案、预防

请回复数字选择（如：1）` });
        this.scrollToBottom();
        this.inputMode = "guided";
    }
    openInbox() {
        this.clearEmptyState();
        const msg = this.messagesEl.createDiv({ cls: "kb-message kb-message-system" });
        msg.createEl("pre", { text: `📥 收件箱 - 原始素材快速捕获

这里是你科研灵感和碎片知识的快速入口。

💡 使用场景：
• 看到一个有价值的观点，先记下来
• 实验中的灵感，随时抓拍
• 读到的关键信息片段
• 任何想记录但还没整理的内容

📝 使用方法：
直接输入内容即可，我会自动保存到收件箱。

🔄 定期整理：
我会定期帮你整理收件箱的内容，生成正式的文档。

📌 操作提示：
• 直接输入内容 → 保存到收件箱
• 输入"整理" → 查看待整理的收件箱内容
• 输入"退出" → 退出收件箱模式

现在开始记录吧！` });
        this.scrollToBottom();
        this.inputMode = "inbox";
    }
    async handleGuidedInput(query) {
        // Handle inbox mode - quick save
        if (this.inputMode === "inbox") {
            if (query.toLowerCase() === "退出" || query.toLowerCase() === "quit") {
                this.inputMode = "normal";
                this.addSystemMessage("已退出收件箱模式");
                return true;
            }
            if (query.toLowerCase() === "整理") {
                await this.organizeInbox();
                return true;
            }
            const result = await this.saveToInbox(query);
            this.addSystemMessage(`✅ 已保存到收件箱：\n📄 ${result}\n\n继续输入内容，或输入"整理"查看待整理内容`);
            return true;
        }
        if (this.inputMode !== "guided")
            return false;
        const step = this.guidedStep;
        const data = this.guidedData;
        if (step === 0) {
            // Step 1: Select type
            const typeMap = {
                "1": "experiment",
                "2": "literature",
                "3": "concept",
                "4": "protocol",
                "5": "problem",
            };
            const type = typeMap[query];
            if (!type) {
                this.addSystemMessage("❌ 请选择有效的数字（1-5）");
                return true;
            }
            data.type = type;
            const typeNames = {
                experiment: "实验记录",
                literature: "文献笔记",
                concept: "概念卡片",
                protocol: "实验方案",
                problem: "问题案例",
            };
            this.guidedStep = 1;
            this.addSystemMessage(`✅ 已选择：${typeNames[type]}\n\n请输入标题：`);
            return true;
        }
        if (step === 1) {
            // Step 2: Get title
            data.title = query;
            this.guidedStep = 2;
            const prompts = {
                experiment: "请描述实验目的和主要步骤：",
                literature: "请提供文献标题、作者和核心观点：",
                idea: "请详细描述你的想法：",
                problem: "请描述遇到的问题：",
                learning: "请描述学到的知识点：",
            };
            this.addSystemMessage(prompts[data.type]);
            return true;
        }
        if (step === 2) {
            // Step 3: Get content
            data.content = query;
            this.guidedStep = 3;
            const prompts = {
                experiment: "实验结果如何？（成功/失败/进行中）",
                literature: "这篇文献对你的研究有什么启示？",
                concept: "这个概念的核心机制是什么？",
                protocol: "实验需要哪些关键试剂和设备？",
                problem: "你尝试了哪些解决方案？效果如何？",
            };
            this.addSystemMessage(prompts[data.type] || "请补充任何其他相关信息（或回复'完成'结束）：");
            return true;
        }
        if (step === 3) {
            // Step 4: Get results/notes
            data.notes = query;
            // Save the guided input
            const result = await this.saveGuidedInput(data);
            this.addSystemMessage(`✅ 已保存！\n\n📄 文件：${result}\n📁 类型：${data.type}\n📝 标题：${data.title}`);
            // Reset guided mode
            this.inputMode = "normal";
            this.guidedStep = 0;
            this.guidedData = {};
            return true;
        }
        return false;
    }
    async saveGuidedInput(data) {
        const date = new Date();
        const dateStr = date.toISOString().split("T")[0];
        const timeStr = date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
        const typeMap = {
            experiment: "01_输入区/实验记录",
            literature: "01_输入区/文献笔记",
            concept: "02_知识加工区/概念卡片",
            protocol: "02_知识加工区/实验方法库",
            problem: "02_知识加工区/问题与解决方案",
        };
        const tagMap = {
            experiment: ["实验记录", "正式文档"],
            literature: ["文献笔记", "正式文档"],
            concept: ["概念", "正式文档"],
            protocol: ["实验方法", "正式文档"],
            problem: ["问题案例", "正式文档"],
        };
        const folder = typeMap[data.type];
        const tags = tagMap[data.type];
        const content = `---
date: ${dateStr}
time: ${timeStr}
tags:
${tags.map((t) => `  - ${t}`).join("\n")}
type: ${data.type}
source: guided-input
---

# ${data.title}

> 输入时间：${dateStr} ${timeStr}
> 输入方式：引导式输入

## 内容

${data.content}

## 补充说明

${data.notes || "无"}

---
*此文档由知识库助手引导输入生成*
`;
        const filePath = `${folder}/${dateStr}_${data.title.substring(0, 30)}.md`;
        // @ts-ignore
        await this.app.vault.create(filePath, content);
        return filePath;
    }
    async saveToInbox(content) {
        const date = new Date();
        const dateStr = date.toISOString().split("T")[0];
        const timeStr = date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
        // Extract title from first line or first 30 chars
        const firstLine = content.split("\n")[0];
        const title = firstLine.substring(0, 50).replace(/[^\w一-龥]/g, "_") || "未命名";
        const folder = "01_输入区/收件箱";
        const fileContent = `---
date: ${dateStr}
time: ${timeStr}
tags:
  - 收件箱
  - 原始素材
type: inbox
source: quick-input
status: pending
---

# ${title}

> 输入时间：${dateStr} ${timeStr}
> 输入方式：收件箱快速输入
> 状态：待整理

## 内容

${content}

---
*此文档由知识库助手收件箱快速生成，待 AI 整理*
`;
        const filePath = `${folder}/${dateStr}_${timeStr.replace(":", "")}_${title.substring(0, 20)}.md`;
        // @ts-ignore
        await this.app.vault.create(filePath, fileContent);
        return filePath;
    }
    async organizeInbox() {
        // @ts-ignore
        const files = this.app.vault.getFiles().filter((f) => f.path.includes("01_输入区/收件箱"));
        if (files.length === 0) {
            this.addSystemMessage("📭 收件箱为空，没有待整理的内容");
            return;
        }
        let msg = `📬 收件箱整理\n\n`;
        msg += `待整理内容：${files.length} 条\n\n`;
        // Group by date
        const byDate = {};
        files.forEach((f) => {
            const date = f.basename.split("_")[0];
            if (!byDate[date])
                byDate[date] = [];
            byDate[date].push(f);
        });
        for (const [date, dateFiles] of Object.entries(byDate)) {
            msg += `📅 ${date}\n`;
            dateFiles.forEach((f) => {
                const title = f.basename.replace(/^\d{4}-\d{2}-\d{2}_\d{4}_/, "");
                msg += `  • ${title}\n`;
            });
            msg += "\n";
        }
        msg += "💡 建议操作：\n";
        msg += "• 输入\"整理 [日期]\" - 整理某天的内容\n";
        msg += "• 输入\"全部整理\" - 整理所有内容\n";
        msg += "• 输入\"退出\" - 退出收件箱模式";
        this.addSystemMessage(msg);
    }
    async onClose() { }
}
class KBPluginSettingTab extends obsidian_1.PluginSettingTab {
    constructor(app, plugin) {
        super(app, plugin);
        this.plugin = plugin;
    }
    display() {
        const { containerEl } = this;
        containerEl.empty();
        containerEl.createEl("h2", { text: "知识库助手设置" });
        new obsidian_1.Setting(containerEl)
            .setName("后端端口")
            .setDesc("KB Backend 服务端口号（默认 8000）")
            .addText((text) => text
            .setPlaceholder("8000")
            .setValue(String(this.plugin.settings.backendPort))
            .onChange(async (value) => {
            const port = parseInt(value);
            if (!isNaN(port) && port > 0 && port < 65536) {
                this.plugin.settings.backendPort = port;
                await this.plugin.saveSettings();
                (0, api_1.setApiBase)(`http://localhost:${port}`);
            }
        }));
        new obsidian_1.Setting(containerEl)
            .setName("后端路径")
            .setDesc("main.py 的完整路径（留空则自动检测为 vault 下 kb-backend/main.py）")
            .addText((text) => text
            .setPlaceholder("自动检测")
            .setValue(this.plugin.settings.backendPath)
            .onChange(async (value) => {
            this.plugin.settings.backendPath = value;
            await this.plugin.saveSettings();
        }));
        new obsidian_1.Setting(containerEl)
            .setName("自动启动后端")
            .setDesc("插件加载时自动尝试启动后端服务")
            .addToggle((toggle) => toggle
            .setValue(this.plugin.settings.autoStart)
            .onChange(async (value) => {
            this.plugin.settings.autoStart = value;
            await this.plugin.saveSettings();
        }));
    }
}
class KBPlugin extends obsidian_1.Plugin {
    constructor() {
        super(...arguments);
        this.settings = DEFAULT_SETTINGS;
    }
    async onload() {
        await this.loadSettings();
        (0, api_1.setApiBase)(`http://localhost:${this.settings.backendPort}`);
        this.registerView(VIEW_TYPE_KB_CHAT, (leaf) => new ChatView(leaf));
        this.addRibbonIcon("bot", "知识库助手", () => {
            this.activateView();
        });
        this.addCommand({
            id: "open-kb-chat",
            name: "打开知识库助手",
            callback: () => this.activateView(),
        });
        this.addCommand({
            id: "kb-show-status",
            name: "知识库助手: 显示状态",
            callback: () => this.showStatusInChat(),
        });
        this.addCommand({
            id: "kb-show-progress",
            name: "知识库助手: 显示进度",
            callback: () => this.showProgressInChat(),
        });
        this.addCommand({
            id: "kb-suggest-links",
            name: "知识库助手: 推荐相关链接",
            callback: () => this.suggestLinksForCurrentNote(),
        });
        this.addSettingTab(new KBPluginSettingTab(this.app, this));
        // Auto-start backend on plugin load
        if (this.settings.autoStart) {
            this.startBackend();
        }
    }
    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }
    async saveSettings() {
        await this.saveData(this.settings);
    }
    async startBackend() {
        try {
            // Check if backend is already running
            const response = await fetch(`${(0, api_1.getApiBase)()}/api/status`, {
                method: "GET",
                signal: AbortSignal.timeout(2000)
            });
            if (response.ok) {
                console.log("KB Backend already running");
                return;
            }
        }
        catch {
            // Backend not running, try to start it
        }
        // Resolve backend path: setting > auto-detect (vault/kb-backend/main.py)
        let backendPath = this.settings.backendPath;
        if (!backendPath) {
            const vaultPath = this.app.vault.adapter?.basePath || "";
            if (vaultPath) {
                backendPath = `${vaultPath}\\00_系统\\kb-backend\\main.py`;
            }
        }
        if (!backendPath) {
            console.warn("KB Backend path not configured and cannot auto-detect");
            return;
        }
        // Start backend using Node.js child_process
        try {
            const { exec } = require("child_process");
            exec(`python "${backendPath}"`, (error) => {
                if (error) {
                    console.error("Failed to start KB Backend:", error.message);
                }
            });
            console.log(`KB Backend starting from ${backendPath}...`);
        }
        catch (err) {
            console.error("Failed to start KB Backend:", err);
        }
    }
    async activateView() {
        const existing = this.app.workspace.getLeavesOfType(VIEW_TYPE_KB_CHAT);
        if (existing.length > 0) {
            this.app.workspace.revealLeaf(existing[0]);
            return;
        }
        const leaf = this.app.workspace.getRightLeaf(false);
        if (leaf) {
            await leaf.setViewState({ type: VIEW_TYPE_KB_CHAT, active: true });
            this.app.workspace.revealLeaf(leaf);
        }
    }
    async showStatusInChat() {
        await this.activateView();
    }
    async showProgressInChat() {
        await this.activateView();
    }
    async suggestLinksForCurrentNote() {
        await this.activateView();
        // Get the active ChatView to display messages
        const leaves = this.app.workspace.getLeavesOfType(VIEW_TYPE_KB_CHAT);
        const chatView = leaves[0]?.view;
        if (!chatView)
            return;
        // Get current active file
        const activeFile = this.app.workspace.getActiveFile();
        if (!activeFile) {
            chatView.addSystemMessage("⚠️ 请先打开一个笔记文件");
            return;
        }
        // Read file content
        const content = await this.app.vault.read(activeFile);
        const title = activeFile.basename;
        chatView.addSystemMessage(`🔍 正在分析笔记: ${title}...`);
        try {
            const response = await fetch(`${(0, api_1.getApiBase)()}/api/entities/recognize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: content }),
            });
            const data = await response.json();
            if (data.links && data.links.length > 0) {
                let msg = `📎 为 "${title}" 推荐以下链接：\n\n`;
                data.links.forEach((link) => {
                    msg += `• ${link}\n`;
                });
                msg += "\n💡 在笔记中输入 [[链接名]] 即可创建链接";
                chatView.addSystemMessage(msg);
            }
            else {
                chatView.addSystemMessage("ℹ️ 未识别到可链接的概念");
            }
        }
        catch (err) {
            chatView.addSystemMessage(`❌ 分析失败: ${err}`);
        }
    }
    onunload() { }
}
exports.default = KBPlugin;
