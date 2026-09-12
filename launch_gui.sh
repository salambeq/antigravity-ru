#!/usr/bin/env bash
# ==============================================================================
#           ANTIGRAVITY TOOLKIT GUI — СКРИПТ БЫСТРОГО ЗАПУСКА
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ "$1" == "--app" ] || [ "$1" == "--dist" ]; then
    if [ -d "dist/Antigravity Toolkit GUI.app" ]; then
        echo "🚀 Запуск собранного приложения dist/Antigravity Toolkit GUI.app..."
        open "dist/Antigravity Toolkit GUI.app"
        exit 0
    else
        echo "⚠️ Бандл не собран. Запустите ./build_gui_macos.sh"
    fi
fi

if ! command -v npx &> /dev/null; then
    echo "❌ Ошибка: для работы графического интерфейса требуется Node.js (npx)."
    echo "Установите Node.js: brew install node"
    exit 1
fi

echo "🚀 Запуск Antigravity Toolkit GUI (Electron 2.0)..."
exec npx electron . "$@"
