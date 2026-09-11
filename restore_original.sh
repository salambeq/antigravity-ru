#!/bin/bash
set -e

echo "Восстановление оригинальных файлов Antigravity..."

APP_DIR="/Applications/Antigravity.app/Contents/Resources"

if [ -f "$APP_DIR/app.asar.orig" ]; then
    cp -f "$APP_DIR/app.asar.orig" "$APP_DIR/app.asar"
    echo "✓ app.asar восстановлен"
else
    echo "⚠ Резервная копия app.asar.orig не найдена!"
fi

if [ -f "$APP_DIR/bin/language_server.orig" ]; then
    cp -f "$APP_DIR/bin/language_server.orig" "$APP_DIR/bin/language_server"
    codesign --force --deep --sign - "$APP_DIR/bin/language_server"
    echo "✓ language_server восстановлен и подписан"
else
    echo "⚠ Резервная копия language_server.orig не найдена!"
fi

echo "Готово. Перезапустите Antigravity."
