# ==============================================================================
# Antigravity Toolkit Launcher for Windows PowerShell
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir\main.py" $args
