@echo off
REM ==============================================================================
REM Antigravity Toolkit Launcher for Windows
REM Официальный репозиторий: https://github.com/salambeq/antigravity-ru
REM ==============================================================================
setlocal
set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%main.py" %*
endlocal
