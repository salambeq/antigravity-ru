#!/bin/bash
set -e

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

echo "Восстановление оригинальных файлов Antigravity..."
echo "Каталог ресурсов: $APP_DIR"

if [ -f "$APP_DIR/app.asar.orig" ]; then
    cp -f "$APP_DIR/app.asar.orig" "$APP_DIR/app.asar"
    echo "✓ app.asar восстановлен"
else
    echo "⚠ Резервная копия app.asar.orig не найдена!"
fi

if [ -f "$APP_DIR/bin/language_server.orig" ]; then
    cp -f "$APP_DIR/bin/language_server.orig" "$APP_DIR/bin/language_server"
    if [ "$IS_MAC" = true ]; then
        codesign --force --deep --sign - "$APP_DIR/bin/language_server"
    fi
    echo "✓ language_server восстановлен"
else
    echo "⚠ Резервная копия language_server.orig не найдена!"
fi

echo "Готово. Перезапустите Antigravity."
