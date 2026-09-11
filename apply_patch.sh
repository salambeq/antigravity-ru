#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="/Applications/Antigravity.app/Contents/Resources"
TEMP_DIR="/tmp/antigravity_patch_$$"

echo "=== Antigravity 2.0 Auto-Patcher ==="

if [ ! -d "/Applications/Antigravity.app" ]; then
    echo "❌ Ошибка: /Applications/Antigravity.app не найдено!"
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
mkdir -p "$TEMP_DIR"
trap 'rm -rf "$TEMP_DIR"' EXIT

npx --yes @electron/asar extract "$APP_DIR/app.asar.orig" "$TEMP_DIR/asar"
python3 "$SCRIPT_DIR/patch_asar.py" "$TEMP_DIR/asar/dist"
npx --yes @electron/asar pack "$TEMP_DIR/asar" "$TEMP_DIR/app.asar" --unpack "**/node_modules/chrome-devtools-mcp/**"

cp -f "$TEMP_DIR/app.asar" "$APP_DIR/app.asar"
cp -f "$TEMP_DIR/app.asar" "$SCRIPT_DIR/app.asar.ru"
cp -f "$APP_DIR/bin/language_server" "$SCRIPT_DIR/language_server.ru"

echo "4. Проверка целостности и подписи..."
"$APP_DIR/bin/language_server" --stamp
codesign -v "$APP_DIR/bin/language_server"

echo ""
echo "🎉 Локализация успешно применена!"
echo "Пожалуйста, перезапустите Antigravity (Cmd+Q) для отображения изменений."
