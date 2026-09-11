#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect OS and paths
if [ -n "$ANTIGRAVITY_RESOURCES_PATH" ] && [ -d "$ANTIGRAVITY_RESOURCES_PATH" ]; then
    APP_DIR="$ANTIGRAVITY_RESOURCES_PATH"
elif [ "$(uname)" = "Darwin" ]; then
    APP_DIR="/Applications/Antigravity.app/Contents/Resources"
    IS_MAC=true
else
    IS_MAC=false
    if [ -d "/opt/Antigravity/resources" ]; then
        APP_DIR="/opt/Antigravity/resources"
    elif [ -d "$HOME/.local/share/antigravity/resources" ]; then
        APP_DIR="$HOME/.local/share/antigravity/resources"
    elif [ -d "/usr/lib/antigravity/resources" ]; then
        APP_DIR="/usr/lib/antigravity/resources"
    else
        APP_DIR="/opt/Antigravity/resources"
    fi
fi

echo "=== Antigravity 2.0 Auto-Patcher ==="
echo "Целевой каталог ресурсов: $APP_DIR"

if [ ! -d "$APP_DIR" ]; then
    echo "❌ Ошибка: Каталог ресурсов Antigravity не найден: $APP_DIR"
    echo "Если программа установлена в нестандартную папку, укажите: export ANTIGRAVITY_RESOURCES_PATH=/путь/к/resources"
    exit 1
fi

echo "1. Проверка и создание резервных копий..."
if [ ! -f "$APP_DIR/app.asar.orig" ]; then
    cp "$APP_DIR/app.asar" "$APP_DIR/app.asar.orig"
    echo "  ✓ Создан $APP_DIR/app.asar.orig"
fi
if [ ! -f "$APP_DIR/bin/language_server.orig" ]; then
    cp "$APP_DIR/bin/language_server" "$APP_DIR/bin/language_server.orig"
    echo "  ✓ Создан $APP_DIR/bin/language_server.orig"
fi

echo "2. Локализация language_server..."
python3 "$SCRIPT_DIR/patch_binary.py"

echo "3. Локализация app.asar..."
TEMP_DIR="/tmp/antigravity_patch_$$"
mkdir -p "$TEMP_DIR"
trap 'rm -rf "$TEMP_DIR"' EXIT

npx --yes @electron/asar extract "$APP_DIR/app.asar.orig" "$TEMP_DIR/asar"
python3 "$SCRIPT_DIR/patch_asar.py" "$TEMP_DIR/asar/dist"
npx --yes @electron/asar pack "$TEMP_DIR/asar" "$TEMP_DIR/app.asar" --unpack "**/node_modules/chrome-devtools-mcp/**"

cp -f "$TEMP_DIR/app.asar" "$APP_DIR/app.asar"
cp -f "$TEMP_DIR/app.asar" "$SCRIPT_DIR/app.asar.ru"
cp -f "$APP_DIR/bin/language_server" "$SCRIPT_DIR/language_server.ru"

echo "4. Проверка целостности..."
"$APP_DIR/bin/language_server" --stamp
if [ "$IS_MAC" = true ]; then
    codesign -v "$APP_DIR/bin/language_server"
fi

echo ""
echo "🎉 Локализация успешно применена!"
echo "Пожалуйста, перезапустите Antigravity для отображения изменений."
