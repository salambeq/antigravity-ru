# Restore Original Antigravity Files (Windows PowerShell)
$ErrorActionPreference = "Stop"

function Get-AntigravityResources {
    if ($env:ANTIGRAVITY_RESOURCES_PATH -and (Test-Path $env:ANTIGRAVITY_RESOURCES_PATH)) {
        return $env:ANTIGRAVITY_RESOURCES_PATH
    }
    $localApp = [System.Environment]::GetFolderPath("LocalApplicationData")
    $p1 = Join-Path $localApp "Programs\Antigravity\resources"
    if (Test-Path $p1) { return $p1 }

    $p2 = "C:\Program Files\Antigravity\resources"
    if (Test-Path $p2) { return $p2 }

    Write-Error "Antigravity resources directory not found."
}

$AppRes = Get-AntigravityResources
Write-Host "Восстановление оригинальных файлов Antigravity..." -ForegroundColor Cyan

$OrigAsar = Join-Path $AppRes "app.asar.orig"
$OrigBin = Join-Path $AppRes "bin\language_server.exe.orig"

if (Test-Path $OrigAsar) {
    Copy-Item -Force $OrigAsar (Join-Path $AppRes "app.asar")
    Write-Host "✓ app.asar восстановлен" -ForegroundColor Green
}
if (Test-Path $OrigBin) {
    Copy-Item -Force $OrigBin (Join-Path $AppRes "bin\language_server.exe")
    Write-Host "✓ language_server.exe восстановлен" -ForegroundColor Green
}

Write-Host "Готово. Перезапустите Antigravity." -ForegroundColor Green
