# Antigravity Toolkit Launcher for Windows PowerShell
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$ScriptDir\main.py" $args
