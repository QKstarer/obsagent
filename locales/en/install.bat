@echo off
chcp 65001 >nul
echo ========================================
echo   KB Assistant - One-Click Install
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python installed

:: Check Ollama
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama not found. Please install Ollama
    echo Download: https://ollama.com/download
    pause
    exit /b 1
)
echo [OK] Ollama installed

:: Install Python dependencies
echo.
echo [1/3] Installing Python dependencies...
pip install -r kb-backend\requirements.txt -q
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: Pull models
echo.
echo [2/3] Pulling AI models (first time ~5GB download)...
echo       Already downloaded models will be skipped
ollama pull nomic-embed-text
ollama pull deepseek-r1:7b
echo [OK] Models ready

:: Create start script
echo.
echo [3/3] Creating start script...
(
echo @echo off
echo chcp 65001 ^>nul
echo echo Starting KB Assistant backend...
echo cd /d "%%~dp0kb-backend"
echo set LANG=en
echo python main.py
echo pause
) > start-backend.bat
echo [OK] Start script created

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Usage:
echo   1. Copy kb-plugin folder to Obsidian plugins directory
echo   2. Enable plugin in Obsidian
echo   3. Double-click start-backend.bat to start backend
echo.
pause
