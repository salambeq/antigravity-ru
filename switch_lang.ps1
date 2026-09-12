# ==============================================================================
# Language Switcher for Antigravity 2.0 (Windows PowerShell)
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("ru", "en")]
    [string]$Language
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Get-AntigravityResources {
    if ($env:ANTIGRAVITY_RESOURCES_PATH -and (Test-Path $env:ANTIGRAVITY_RESOURCES_PATH)) {
        return $env:ANTIGRAVITY_RESOURCES_PATH
    }
    $localApp = [System.Environment]::GetFolderPath("LocalApplicationData")
    $p1 = Join-Path $localApp "Programs\Antigravity\resources"
    if (Test-Path $p1) { return $p1 }

    $p2 = "C:\Program Files\Antigravity\resources"
    if (Test-Path $p2) { return $p2 }

    Write-Error "Antigravity resources directory not found. Please set `$env:ANTIGRAVITY_RESOURCES_PATH."
}

$AppRes = Get-AntigravityResources

if ($Language -eq "ru") {
    Write-Host "🔄 Переключение интерфейса на РУССКИЙ язык..." -ForegroundColor Cyan
    $RuAsar = Join-Path $ScriptDir "app.asar.ru"
    $RuBin = Join-Path $ScriptDir "language_server.ru.exe"
    
    if (-not (Test-Path $RuAsar) -or -not (Test-Path $RuBin)) {
        Write-Host "Файлы локализации не найдены. Запуск сборки патча..."
        & "$ScriptDir\apply_patch.ps1"
    } else {
        Copy-Item -Force $RuAsar (Join-Path $AppRes "app.asar")
        Copy-Item -Force $RuBin (Join-Path $AppRes "bin\language_server.exe")
    }
    Write-Host "✅ Интерфейс Antigravity переключен на РУССКИЙ! Перезапустите приложение." -ForegroundColor Green
}
elseif ($Language -eq "en") {
    Write-Host "🔄 Переключение интерфейса на АНГЛИЙСКИЙ язык..." -ForegroundColor Cyan
    $OrigAsar = Join-Path $AppRes "app.asar.orig"
    $OrigBin = Join-Path $AppRes "bin\language_server.exe.orig"

    if (Test-Path $OrigAsar) {
        Copy-Item -Force $OrigAsar (Join-Path $AppRes "app.asar")
    }
    if (Test-Path $OrigBin) {
        Copy-Item -Force $OrigBin (Join-Path $AppRes "bin\language_server.exe")
    }
    Write-Host "✅ Интерфейс Antigravity переключен на АНГЛИЙСКИЙ! Перезапустите приложение." -ForegroundColor Green
}
