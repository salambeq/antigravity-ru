#!/usr/bin/env bash
# ==============================================================================
# Скрипт локальной сборки Antigravity Toolkit для macOS (.app и бинарник)
# Официальный репозиторий: https://github.com/salambeq/antigravity-ru
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Сборка Antigravity Toolkit для macOS ==="

# 1. Проверка и установка PyInstaller
if ! command -v pyinstaller &> /dev/null && [ ! -f "$HOME/Library/Python/3.9/bin/pyinstaller" ]; then
    echo "Установка PyInstaller..."
    python3 -m pip install --user pyinstaller
fi

PYINSTALLER_BIN="pyinstaller"
if [ -f "$HOME/Library/Python/3.9/bin/pyinstaller" ]; then
    PYINSTALLER_BIN="$HOME/Library/Python/3.9/bin/pyinstaller"
fi

# 2. Очистка старых сборок
rm -rf build dist

# 3. Сборка исполняемого файла через PyInstaller
echo "Компиляция бинарника через PyInstaller..."
"$PYINSTALLER_BIN" \
    --noconfirm \
    --clean \
    --onefile \
    --name "Antigravity_Toolkit" \
    --add-data "frontend_bundle:frontend_bundle" \
    --add-data "rules:rules" \
    --add-data "skills:skills" \
    --add-data "patch_asar.py:." \
    --add-data "localize_frontend.py:." \
    --hidden-import=packaging \
    --hidden-import=packaging.version \
    --hidden-import=packaging.specifiers \
    --hidden-import=packaging.requirements \
    --hidden-import=patch_asar \
    --hidden-import=localize_frontend \
    --hidden-import=patcher.accounts \
    --hidden-import=patcher.accounts.keychain \
    --hidden-import=patcher.accounts.manager \
    --hidden-import=patcher.accounts.rotator \
    main.py

# Создаем удобный симлинк / копию antigravity-tool в dist
cp dist/Antigravity_Toolkit dist/antigravity-tool

# 4. Создание нативного macOS Application Bundle (.app)
APP_NAME="Antigravity Toolkit.app"
APP_DIR="dist/$APP_NAME"
MACOS_DIR="$APP_DIR/Contents/MacOS"
RESOURCES_DIR="$APP_DIR/Contents/Resources"

echo "Формирование macOS бандла: $APP_DIR..."
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# Переносим бинарник внутрь бандла
cp dist/Antigravity_Toolkit "$MACOS_DIR/Antigravity_Toolkit"
chmod +x "$MACOS_DIR/Antigravity_Toolkit"

# Иконка
if [ -f "/Applications/Antigravity.app/Contents/Resources/icon.icns" ]; then
    cp "/Applications/Antigravity.app/Contents/Resources/icon.icns" "$RESOURCES_DIR/AppIcon.icns"
fi

# Создаем стартовый скрипт launcher (запускает Terminal.app при двойном клике в Finder)
cat << 'EOF' > "$MACOS_DIR/launcher"
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "\"$DIR/Antigravity_Toolkit\""
end tell
APPLESCRIPT
EOF
chmod +x "$MACOS_DIR/launcher"

# Info.plist
cat << 'EOF' > "$APP_DIR/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>ru</string>
    <key>CFBundleDisplayName</key>
    <string>Antigravity Toolkit</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.antigravity.toolkit</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Antigravity Toolkit</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.0.0</string>
    <key>CFBundleVersion</key>
    <string>2.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "APPL????" > "$APP_DIR/Contents/PkgInfo"

# 5. Подпись через Apple codesign
echo "Подписание бандла через Apple codesign..."
codesign --force --deep --sign - "$APP_DIR"
codesign --force --sign - "dist/Antigravity_Toolkit"
codesign --force --sign - "dist/antigravity-tool"

echo ""
echo "🎉 Сборка успешно завершена!"
echo ""
echo "Собранные файлы для локального использования:"
echo "  1. Приложение для macOS (двойной клик в Finder):"
echo "     👉 $SCRIPT_DIR/dist/Antigravity Toolkit.app"
echo "     (Можно перетащить в папку /Applications)"
echo ""
echo "  2. Автономный консольный бинарник (запуск из терминала):"
echo "     👉 $SCRIPT_DIR/dist/antigravity-tool"
echo "     (Не требует установленного Python или внешних модулей)"
echo ""
