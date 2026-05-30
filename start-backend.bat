@echo off
chcp 65001 >nul
echo ========================================
echo   知识库助手 - 后端服务
echo ========================================
echo.
echo 正在启动后端服务...
echo 端口: 8000
echo 按 Ctrl+C 停止服务
echo.
cd /d "%~dp0kb-backend"
python main.py
pause
