@echo off
chcp 65001 >nul
echo ========================================
echo   知识库助手 - 一键安装
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请安装 Python 3.9+
    pause
    exit /b 1
)
echo [✓] Python 已安装

ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Ollama，请安装 Ollama
    pause
    exit /b 1
)
echo [✓] Ollama 已安装

echo [1/3] 安装依赖...
pip install -r kb-backend\requirements.txt -q
echo [✓] 依赖完成

echo [2/3] 拉取模型...
ollama pull nomic-embed-text
ollama pull deepseek-r1:7b
echo [✓] 模型完成

echo [3/3] 创建启动脚本...
(
echo @echo off
echo cd /d "%%~dp0kb-backend"
echo set LANG=zh
echo python main.py
echo pause
) > start-backend.bat
echo [✓] 完成

echo.
echo 安装完成！双击 start-backend.bat 启动
pause
