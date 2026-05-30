@echo off
chcp 65001 >nul
echo ========================================
echo   KB Assistant - One-Click Install
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.9+
    pause
    exit /b 1
)
echo [OK] Python installed

ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama not found. Install Ollama
    pause
    exit /b 1
)
echo [OK] Ollama installed

echo [1/3] Installing dependencies...
pip install -r kb-backend\requirements.txt -q
echo [OK] Dependencies done

echo [2/3] Pulling models...
ollama pull nomic-embed-text
ollama pull deepseek-r1:7b
echo [OK] Models done

echo [3/3] Creating start script...
(
echo @echo off
echo cd /d "%%~dp0kb-backend"
echo set LANG=en
echo python main.py
echo pause
) > start-backend.bat
echo [OK] Done

echo.
echo Installation complete! Double-click start-backend.bat to run
pause
