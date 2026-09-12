# ==============================================================================
# Antigravity 2.0 Auto-Patcher for Windows (PowerShell)
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
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
Write-Host "=== Antigravity 2.0 Auto-Patcher (Windows) ===" -ForegroundColor Cyan
Write-Host "Официальный репозиторий: https://github.com/salambeq/antigravity-ru" -ForegroundColor Yellow
Write-Host "Resources: $AppRes"

# 1. Backup
$OrigAsar = Join-Path $AppRes "app.asar.orig"
$CurrAsar = Join-Path $AppRes "app.asar"
$OrigBin = Join-Path $AppRes "bin\language_server.exe.orig"
$CurrBin = Join-Path $AppRes "bin\language_server.exe"

if (-not (Test-Path $OrigAsar)) {
    Copy-Item $CurrAsar $OrigAsar
    Write-Host "✓ Created $OrigAsar" -ForegroundColor Green
}
if (-not (Test-Path $OrigBin)) {
    Copy-Item $CurrBin $OrigBin
    Write-Host "✓ Created $OrigBin" -ForegroundColor Green
}

# 2. Patch binary
Write-Host "2. Patching language_server.exe..." -ForegroundColor Yellow
python "$ScriptDir\patch_binary.py"

# 3. Patch app.asar
Write-Host "3. Patching app.asar..." -ForegroundColor Yellow
$TempDir = Join-Path $env:TEMP ("antigravity_patch_" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempDir | Out-Null

try {
    $AsarExtract = Join-Path $TempDir "asar"
    $NewAsar = Join-Path $TempDir "app.asar"
    
    npx --yes @electron/asar extract $OrigAsar $AsarExtract
    python "$ScriptDir\patch_asar.py" (Join-Path $AsarExtract "dist")
    npx --yes @electron/asar pack $AsarExtract $NewAsar --unpack "**/node_modules/chrome-devtools-mcp/**"

    Copy-Item -Force $NewAsar $CurrAsar
    Copy-Item -Force $NewAsar (Join-Path $ScriptDir "app.asar.ru")
    Copy-Item -Force $CurrBin (Join-Path $ScriptDir "language_server.ru.exe")
}
finally {
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
}

Write-Host "🎉 Локализация успешно применена! Перезапустите Antigravity." -ForegroundColor Green
