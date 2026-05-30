@echo off
chcp 65001 >nul
echo ========================================
echo   知识库助手 - 一键安装脚本
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [✓] Python 已安装

:: 检查 Ollama
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Ollama，请先安装 Ollama
    echo 下载地址: https://ollama.com/download
    pause
    exit /b 1
)
echo [✓] Ollama 已安装

:: 安装 Python 依赖
echo.
echo [1/3] 安装 Python 依赖...
pip install -r kb-backend\requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [✓] 依赖安装完成

:: 拉取模型
echo.
echo [2/3] 拉取 AI 模型（首次需要下载约 5GB，请耐心等待）...
echo       如果已下载会自动跳过
ollama pull nomic-embed-text
ollama pull qwen2.5:7b
echo [✓] 模型准备完成

:: 创建启动脚本
echo.
echo [3/3] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo 正在启动知识库助手后端...
echo cd /d "%%~dp0kb-backend"
echo python main.py
echo pause
) > start-backend.bat
echo [✓] 启动脚本创建完成

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 使用方法：
echo   1. 将 kb-plugin 文件夹复制到 Obsidian 插件目录：
echo      ^<Vault路径^>\.obsidian\plugins\kb-plugin\
echo   2. 在 Obsidian 中启用插件
echo   3. 双击 start-backend.bat 启动后端
echo.
echo 详细说明请查看：知识库助手使用说明.md
echo.
pause
