#!/usr/bin/env bash
# ==============================================================================
#      ПУБЛИКАЦИЯ РЕЛИЗА И ДИСТРИБУТИВОВ MACOS (DMG/ZIP) НА GITHUB
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

REPO="salambeq/antigravity-ru"
TAG="v2.0.4"
NAME="Antigravity Toolkit GUI v2.0.4 (macOS Edition)"

ARCH="$(uname -m)"
DMG_PATH="dist/Antigravity-Toolkit-GUI-macOS-${ARCH}.dmg"
ZIP_PATH="dist/Antigravity-Toolkit-GUI-macOS-${ARCH}.zip"

if [ ! -f "$DMG_PATH" ] || [ ! -f "$ZIP_PATH" ]; then
    echo "📦 Файлы дистрибутива не найдены. Запуск пакетирования..."
    ./scripts/package_macos.sh
fi

echo "🔑 Получение токена доступа GitHub..."
TOKEN_RAW=$(git credential-osxkeychain get <<EOF
host=github.com
protocol=https
EOF
)
TOKEN=$(echo "$TOKEN_RAW" | grep '^password=' | cut -d= -f2)

if [ -z "$TOKEN" ]; then
    echo "❌ Ошибка: токен GitHub не найден в Keychain."
    exit 1
fi

echo "🚀 Проверка существования релиза $TAG в репозитории $REPO..."
EXISTING_RELEASE=$(curl -s -H "Authorization: token $TOKEN" \
    -H "User-Agent: AntigravityToolkit" \
    "https://api.github.com/repos/$REPO/releases/tags/$TAG")

RELEASE_ID=$(echo "$EXISTING_RELEASE" | grep -o '"id": [0-9]*' | head -1 | awk '{print $2}')

BODY_TEXT='## 🇷🇺 Antigravity Toolkit GUI v2.0.4 (macOS)

Готовый бинарный дистрибутив десктопного приложения **Antigravity Toolkit GUI** для macOS (Apple Silicon).

### 📦 Загрузка дистрибутива (Пакеты macOS):
- **💿 Образ установщика DMG (рекомендуется)**: [Antigravity-Toolkit-GUI-macOS-arm64.dmg](https://github.com/salambeq/antigravity-ru/releases/download/v2.0.4/Antigravity-Toolkit-GUI-macOS-arm64.dmg)
- **🗜️ Портативный архив ZIP**: [Antigravity-Toolkit-GUI-macOS-arm64.zip](https://github.com/salambeq/antigravity-ru/releases/download/v2.0.4/Antigravity-Toolkit-GUI-macOS-arm64.zip)

---

### ✨ Ключевые возможности релиза:
1. 🎨 **Премиальный графический интерфейс (Obsidian Dark)**:
   - Полный визуальный редизайн в фирменном стиле Antigravity 2.0.
   - Эффекты матового стекла (glassmorphism), неоновые акценты Cyan / Emerald / Indigo.
   - Интерактивный Bento Grid, живая консоль операций и нативные окна подтверждений.
2. 🔒 **100% Локальность и приватность (Zero-Leak Policy)**:
   - Полное отсутствие фоновой телеметрии и внешних сетевых запросов в рантайме.
   - Офлайн-декодирование профиля Google OAuth из локального `id_token` без обращений к Google API.
   - Все базы данных диалогов, токены и архивы надежно изолированы и защищены в `.gitignore`.
3. 📦 **Защита и резервное копирование чатов (Backup & Restore)**:
   - Сохранение 100+ пользовательских диалогов (`conversations/*.db`), сессий и настроек в один клик.
   - Встроенный менеджер списка архивов и мгновенное восстановление переписок.
4. 🔄 **Мультиаккаунты и авто-ротация квот токенов**:
   - Мгновенное переключение между 4 Google-аккаунтами через системный Keychain macOS.
   - Фоновый демон ротации при получении HTTP 429 (`QUOTA_EXHAUSTED`).
5. 🍏 **Нативная интеграция с macOS**:
   - Корректные отступы под системные кнопки управления окном (Traffic Lights).
   - Ad-hoc цифровая подпись Apple `codesign`, исключающая предупреждения о повреждении бандла.'

if [ -z "$RELEASE_ID" ] || [ "$RELEASE_ID" = "null" ]; then
    echo "✨ Создание нового релиза $TAG..."
    JSON_PAYLOAD=$(node -e '
        const body = process.argv[1];
        console.log(JSON.stringify({
            tag_name: "v2.0.4",
            target_commitish: "main",
            name: "Antigravity Toolkit GUI v2.0.4 (macOS Edition)",
            body: body,
            draft: false,
            prerelease: false
        }));
    ' "$BODY_TEXT")

    CREATE_RESP=$(curl -s -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Content-Type: application/json" \
        -H "User-Agent: AntigravityToolkit" \
        -d "$JSON_PAYLOAD" \
        "https://api.github.com/repos/$REPO/releases")

    RELEASE_ID=$(echo "$CREATE_RESP" | grep -o '"id": [0-9]*' | head -1 | awk '{print $2}')
    echo "[+] Релиз создан с ID: $RELEASE_ID"
else
    echo "[+] Найден существующий релиз ID: $RELEASE_ID"
fi

if [ -z "$RELEASE_ID" ] || [ "$RELEASE_ID" = "null" ]; then
    echo "❌ Ошибка создания релиза."
    exit 1
fi

upload_asset() {
    local file="$1"
    local name="$2"
    local mime="$3"
    local size=$(ls -lh "$file" | awk '{print $5}')

    echo "⬆️  Загрузка $name ($size)..."
    curl -s -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Content-Type: $mime" \
        -H "User-Agent: AntigravityToolkit" \
        --data-binary @"$file" \
        "https://uploads.github.com/repos/$REPO/releases/$RELEASE_ID/assets?name=$name" > /dev/null
    echo "✅ Файл $name успешно загружен!"
}

# Удаляем старые ассеты если были с такими именами
ASSETS=$(curl -s -H "Authorization: token $TOKEN" -H "User-Agent: AntigravityToolkit" "https://api.github.com/repos/$REPO/releases/$RELEASE_ID/assets")
for asset_id in $(echo "$ASSETS" | grep -o '"id": [0-9]*' | awk '{print $2}'); do
    curl -s -X DELETE -H "Authorization: token $TOKEN" -H "User-Agent: AntigravityToolkit" "https://api.github.com/repos/$REPO/releases/assets/$asset_id" > /dev/null || true
done

upload_asset "$DMG_PATH" "Antigravity-Toolkit-GUI-macOS-arm64.dmg" "application/octet-stream"
upload_asset "$ZIP_PATH" "Antigravity-Toolkit-GUI-macOS-arm64.zip" "application/zip"

echo "========================================================================"
echo "🎉 ПАКЕТЫ УСПЕШНО РАЗМЕЩЕНЫ НА GITHUB!"
echo "👉 Ссылка на релиз: https://github.com/$REPO/releases/tag/$TAG"
echo "👉 Прямая ссылка на DMG: https://github.com/$REPO/releases/download/$TAG/Antigravity-Toolkit-GUI-macOS-arm64.dmg"
echo "👉 Прямая ссылка на ZIP: https://github.com/$REPO/releases/download/$TAG/Antigravity-Toolkit-GUI-macOS-arm64.zip"
echo "========================================================================"
