#!/usr/bin/env bash
# ==============================================================================
#      СБОРКА ДЕСКТОПНОГО ПРИЛОЖЕНИЯ ANTIGRAVITY TOOLKIT GUI ДЛЯ MACOS
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "========================================================================"
echo "    СБОРКА ЛОКАЛЬНОГО BUNDLE: Antigravity Toolkit GUI.app (macOS)"
echo "========================================================================"

if ! command -v npx &> /dev/null; then
    echo "❌ Ошибка: для сборки требуется npx (Node.js)."
    exit 1
fi

ARCH="$(uname -m)"
if [ "$ARCH" = "x86_64" ]; then
    ELECTRON_ARCH="x64"
else
    ELECTRON_ARCH="arm64"
fi

ELECTRON_VER="44.3.0"

export ELECTRON_CACHE="$HOME/Library/Caches/electron"
export HTTP_PROXY="" HTTPS_PROXY="" ALL_PROXY="" http_proxy="" https_proxy="" all_proxy=""

echo "📦 Архитектура хоста: $ARCH -> Electron arch: $ELECTRON_ARCH (v$ELECTRON_VER)"
echo "📦 Очистка предыдущих сборок в dist/..."
mkdir -p dist
rm -rf dist/Antigravity* 2>/dev/null || true

echo "🔨 Упаковка приложения через @electron/packager..."
npx @electron/packager . "Antigravity Toolkit GUI" \
    --platform=darwin \
    --arch="$ELECTRON_ARCH" \
    --electron-version="$ELECTRON_VER" \
    --out=dist \
    --overwrite \
    --asar=false \
    --prune=true \
    --app-bundle-id="com.antigravity.toolkit.gui" \
    --app-category-type="public.app-category.developer-tools" \
    --icon="gui/icon" \
    --ignore="^/dist($|/)" \
    --ignore="^/\\.git($|/)" \
    --ignore="^/\\.venv($|/)" \
    --ignore="^/build($|/)" \
    --ignore="^/extracted_asar($|/)" \
    --ignore="^/app\\.asar\\.unpacked($|/)" \
    --ignore="^/frontend_bundle($|/)" \
    --ignore="^/language_server.*" \
    --ignore="^/.*\\.pyc$" \
    --ignore="^/__pycache__($|/)"

TARGET_DIR="dist/Antigravity Toolkit GUI-darwin-$ELECTRON_ARCH"
APP_PATH="$TARGET_DIR/Antigravity Toolkit GUI.app"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ Ошибка: бандл $APP_PATH не найден после сборки!"
    exit 1
fi

echo "🔏 Применение ad-hoc цифровой подписи macOS (codesign)..."
codesign --force --deep --sign - "$APP_PATH"

echo "📋 Копирование в удобный путь dist/Antigravity Toolkit GUI.app..."
rm -rf "dist/Antigravity Toolkit GUI.app"
cp -R "$APP_PATH" "dist/Antigravity Toolkit GUI.app"
if [ -f "gui/icon.icns" ]; then
    cp "gui/icon.icns" "dist/Antigravity Toolkit GUI.app/Contents/Resources/electron.icns" 2>/dev/null || true
fi
codesign --force --deep --sign - "dist/Antigravity Toolkit GUI.app"

echo "✅ Проверка цифровой подписи..."
codesign -v "dist/Antigravity Toolkit GUI.app"

echo "========================================================================"
echo "🎉 СБОРКА УСПЕШНО ЗАВЕРШЕНА!"
echo "Приложение готово к локальному запуску:"
echo "👉 dist/Antigravity Toolkit GUI.app"
echo "Размер: $(du -sh 'dist/Antigravity Toolkit GUI.app' | cut -f1)"
echo "Запуск: open 'dist/Antigravity Toolkit GUI.app'"
echo "========================================================================"
