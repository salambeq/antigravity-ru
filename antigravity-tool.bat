@echo off
REM Antigravity Toolkit Launcher for Windows
setlocal
set "SCRIPT_DIR=%~dp0"
python "%SCRIPT_DIR%main.py" %*
endlocal
