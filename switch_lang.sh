#!/bin/bash
# ==============================================================================
# Language Switcher for Antigravity 2.0 (macOS / Linux)
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
set -e

LANG_ARG="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detect OS and paths
if [ -n "$ANTIGRAVITY_RESOURCES_PATH" ] && [ -d "$ANTIGRAVITY_RESOURCES_PATH" ]; then
    APP_RES="$ANTIGRAVITY_RESOURCES_PATH"
elif [ "$(uname)" = "Darwin" ]; then
    APP_RES="/Applications/Antigravity.app/Contents/Resources"
    IS_MAC=true
else
    IS_MAC=false
    if [ -d "/opt/Antigravity/resources" ]; then
        APP_RES="/opt/Antigravity/resources"
    elif [ -d "$HOME/.local/share/antigravity/resources" ]; then
        APP_RES="$HOME/.local/share/antigravity/resources"
    elif [ -d "/usr/lib/antigravity/resources" ]; then
        APP_RES="/usr/lib/antigravity/resources"
    else
        APP_RES="/opt/Antigravity/resources"
    fi
fi

show_usage() {
    echo "Использование: ./switch_lang.sh [ru|en]"
    echo "  ru - Переключить интерфейс Antigravity на русский язык"
    echo "  en - Переключить интерфейс Antigravity на оригинальный английский язык"
    exit 1
}

if [ -z "$LANG_ARG" ]; then
    show_usage
fi

if [ "$LANG_ARG" = "ru" ]; then
    echo "🔄 Переключение на русский язык..."

    if [ ! -f "$SCRIPT_DIR/app.asar.ru" ] || [ ! -f "$SCRIPT_DIR/language_server.ru" ]; then
        echo "Локализованные файлы не найдены в $SCRIPT_DIR. Запуск сборщика патча..."
        "$SCRIPT_DIR/apply_patch.sh"
    else
        cp -f "$SCRIPT_DIR/app.asar.ru" "$APP_RES/app.asar"
        cp -f "$SCRIPT_DIR/language_server.ru" "$APP_RES/bin/language_server"
        if [ "$IS_MAC" = true ]; then
            codesign --force --deep --sign - "$APP_RES/bin/language_server"
        fi
    fi

    echo "✅ Интерфейс Antigravity успешно переключен на РУССКИЙ язык!"
    echo "Пожалуйста, перезапустите Antigravity для применения изменений."

elif [ "$LANG_ARG" = "en" ]; then
    echo "🔄 Переключение на английский язык..."

    if [ -f "$APP_RES/app.asar.orig" ]; then
        cp -f "$APP_RES/app.asar.orig" "$APP_RES/app.asar"
    else
        echo "⚠ Резервная копия app.asar.orig не найдена!"
    fi

    if [ -f "$APP_RES/bin/language_server.orig" ]; then
        cp -f "$APP_RES/bin/language_server.orig" "$APP_RES/bin/language_server"
        if [ "$IS_MAC" = true ]; then
            codesign --force --deep --sign - "$APP_RES/bin/language_server"
        fi
    else
        echo "⚠ Резервная копия language_server.orig не найдена!"
    fi

    echo "✅ Интерфейс Antigravity успешно переключен на АНГЛИЙСКИЙ язык!"
    echo "Пожалуйста, перезапустите Antigravity для применения изменений."

else
    show_usage
fi
