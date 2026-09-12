#!/usr/bin/env bash
# ==============================================================================
#             ПАКЕТИРОВАНИЕ MACOS ВЕРСИИ В DMG И ZIP ДЛЯ GITHUB
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

APP_PATH="dist/Antigravity Toolkit GUI.app"
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Ошибка: бандл $APP_PATH не найден. Сначала выполните сборку."
    ./build_gui_macos.sh
fi

ARCH="$(uname -m)"
ZIP_NAME="Antigravity-Toolkit-GUI-macOS-${ARCH}.zip"
DMG_NAME="Antigravity-Toolkit-GUI-macOS-${ARCH}.dmg"

echo "========================================================================"
echo "    ФОРМИРОВАНИЕ ДИСТРИБУТИВА MACOS (${ARCH}): DMG И ZIP"
echo "========================================================================"

echo "📦 1. Упаковка в ZIP (${ZIP_NAME})..."
rm -f "dist/${ZIP_NAME}"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "dist/${ZIP_NAME}"

echo "💿 2. Создание образа DMG (${DMG_NAME})..."
rm -f "dist/${DMG_NAME}"
DMG_TEMP="dist/dmg_staging"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"
cp -R "$APP_PATH" "$DMG_TEMP/"
ln -s /Applications "$DMG_TEMP/Applications"

hdiutil create \
    -volname "Antigravity Toolkit GUI" \
    -srcfolder "$DMG_TEMP" \
    -ov \
    -format UDZO \
    "dist/${DMG_NAME}"

rm -rf "$DMG_TEMP"

echo "========================================================================"
echo "✅ ДИСТРИБУТИВЫ MACOS УСПЕШНО СОБРАНЫ В dist/:"
ls -lh "dist/${ZIP_NAME}" "dist/${DMG_NAME}"
echo "========================================================================"
