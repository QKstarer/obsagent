@echo off
chcp 65001 >nul

:: Auto-detect language from system locale
for /f "tokens=2" %%i in ('systeminfo ^| findstr /c:"OS Language"') do set LOCALE=%%i
echo %LOCALE% | findstr /i "Chinese" >nul 2>&1
if %errorlevel% equ 0 (
    echo 正在使用中文安装脚本...
    call locales\zh\install.bat
) else (
    echo Using English install script...
    call locales\en\install.bat
)
