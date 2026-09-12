#!/usr/bin/env bash
# ==============================================================================
#      ПУБЛИКАЦИЯ РЕЛИЗА И ДИСТРИБУТИВОВ MACOS (DMG/ZIP) НА GITHUB
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

REPO="salambeq/antigravity-ru"
APP_VER=$(node -p "require('./package.json').version" 2>/dev/null || python3 -c "import json; print(json.load(open('version.json'))['version'])")
TAG="v${APP_VER}"
NAME="Antigravity Toolkit GUI v${APP_VER} (macOS Edition)"

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

# Автоопределение системного прокси macOS для стабильного доступа к GitHub API
CURL_PROXY_ARGS=()
if command -v scutil &>/dev/null; then
    PROXY_ENABLED=$(scutil --proxy | grep -E 'HTTPSEnable\s*:\s*1' || true)
    if [ -n "$PROXY_ENABLED" ]; then
        PROXY_HOST=$(scutil --proxy | grep -E 'HTTPSProxy\s*:' | awk '{print $3}')
        PROXY_PORT=$(scutil --proxy | grep -E 'HTTPSPort\s*:' | awk '{print $3}')
        if [ -n "$PROXY_HOST" ] && [ -n "$PROXY_PORT" ]; then
            CURL_PROXY_ARGS=("-x" "http://${PROXY_HOST}:${PROXY_PORT}")
            echo "[+] Обнаружен системный прокси: http://${PROXY_HOST}:${PROXY_PORT}"
        fi
    fi
fi

# Массив вызова curl с принудительным HTTP/1.1 (предотвращает сбросы соединений в локальных прокси)
CURL_CMD=(curl --http1.1 "${CURL_PROXY_ARGS[@]}")

echo "🚀 Проверка существования релиза $TAG в репозитории $REPO..."
RELEASES_LIST=$("${CURL_CMD[@]}" -s -H "Authorization: token $TOKEN" \
    -H "User-Agent: AntigravityToolkit" \
    "https://api.github.com/repos/$REPO/releases")

RELEASE_ID=$(node -e '
    try {
        const list = JSON.parse(process.argv[1]);
        const r = list.find(x => x.tag_name === process.argv[2]);
        if (r) console.log(r.id);
    } catch (e) {}
' "$RELEASES_LIST" "$TAG")

BODY_TEXT='## 🇷🇺 Antigravity Toolkit GUI v2.0.6 (macOS)

Готовый бинарный дистрибутив десктопного приложения **Antigravity Toolkit GUI** для macOS (Apple Silicon).

### 📦 Загрузка дистрибутива (Пакеты macOS):
- **💿 Образ установщика DMG (рекомендуется)**: [Antigravity-Toolkit-GUI-macOS-arm64.dmg](https://github.com/salambeq/antigravity-ru/releases/download/v2.0.6/Antigravity-Toolkit-GUI-macOS-arm64.dmg)
- **🗜️ Портативный архив ZIP**: [Antigravity-Toolkit-GUI-macOS-arm64.zip](https://github.com/salambeq/antigravity-ru/releases/download/v2.0.6/Antigravity-Toolkit-GUI-macOS-arm64.zip)

---

### ✨ Новые возможности релиза v2.0.6:
1. 🛡️ **Фоновый Keep-Alive 24/7 для всех 4 слотов аккаунтов**:
   - Гарантия от слёта токенов и разлогинивания: если вы активно пользуетесь одним аккаунтом на протяжении нескольких дней, остальные 3 аккаунта остаются активными и валидными благодаря упреждающему обновлению OAuth-токенов в фоновом режиме каждые 20 минут.
   - Мгновенное и бесшовное переключение между всеми 4 Google-профилями без повторного входа в браузере.
2. 🍏 **Интеграция с системным треем macOS (Menu Bar Tray) и Close-to-Tray**:
   - При закрытии на красный крестик окно сворачивается в трей macOS (не прерывая фоновый Keep-Alive и защиту чатов).
   - В меню трея отображается текущий активный слот, email, 5-часовой лимит и таймер сброса.
   - Быстрое переключение любого из 4 аккаунтов прямо из менюбара macOS.
   - Завершение приложения доступно через пункт «Завершить Antigravity Toolkit» в меню трея.
3. ⚡ **Отображение квот токенов для всех 4 слотов одновременно**:
   - На карточке каждого из 4 слотов в реальном времени выводятся остатки 5-часового и недельного лимитов (`⚡ 5ч: X% • 📅 нед: Y%`).
4. 📦 **Защита и бэкап чатов (Backup & Restore)**:
   - Полное сохранение истории диалогов, сессий и конфигураций SQLite (100+ диалогов) локально на диске.
5. 🎨 **Переосмысленный модульный интерфейс (Tabs & Drawer)**:
   - Исправлена верстка и устранены любые перекрытия блоков.
   - Удобная навигация по вкладкам (Панель, Квоты, Аккаунты, Компоненты, Резервные копии).
   - Выдвижная консоль операций (Drawer Terminal) с авто-раскрытием при фоновых процессах.
6. 🔒 **100% Zero-Leak & Офлайн**:
   - Все токены и персональные данные хранятся исключительно локально в Keychain macOS.'

TMP_PAYLOAD="/tmp/github_release_payload.json"

if [ -z "$RELEASE_ID" ] || [ "$RELEASE_ID" = "null" ]; then
    echo "✨ Создание нового релиза $TAG..."
    node -e '
        const fs = require("fs");
        const body = process.argv[1];
        fs.writeFileSync(process.argv[2], JSON.stringify({
            tag_name: "v2.0.6",
            target_commitish: "main",
            name: "Antigravity Toolkit GUI v2.0.6 (macOS Edition)",
            body: body,
            draft: false,
            prerelease: false
        }));
    ' "$BODY_TEXT" "$TMP_PAYLOAD"

    CREATE_RESP=$("${CURL_CMD[@]}" -s -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Content-Type: application/json" \
        -H "User-Agent: AntigravityToolkit" \
        --data-binary @"$TMP_PAYLOAD" \
        "https://api.github.com/repos/$REPO/releases")

    RELEASE_ID=$(echo "$CREATE_RESP" | node -e '
        try {
            const d = JSON.parse(require("fs").readFileSync(0, "utf-8"));
            if (d && d.id) console.log(d.id);
        } catch(e) {}
    ')
    if [ -z "$RELEASE_ID" ] || [ "$RELEASE_ID" = "null" ]; then
        echo "❌ Ошибка создания релиза: $CREATE_RESP"
        exit 1
    fi
    echo "[+] Релиз создан с ID: $RELEASE_ID"
else
    echo "[+] Найден существующий релиз ID: $RELEASE_ID. Обновление описания..."
    node -e '
        const fs = require("fs");
        const body = process.argv[1];
        fs.writeFileSync(process.argv[2], JSON.stringify({
            name: "Antigravity Toolkit GUI v2.0.6 (macOS Edition)",
            body: body
        }));
    ' "$BODY_TEXT" "$TMP_PAYLOAD"

    "${CURL_CMD[@]}" -s -X PATCH \
        -H "Authorization: token $TOKEN" \
        -H "Content-Type: application/json" \
        -H "User-Agent: AntigravityToolkit" \
        --data-binary @"$TMP_PAYLOAD" \
        "https://api.github.com/repos/$REPO/releases/$RELEASE_ID" > /dev/null
    echo "[+] Описание релиза успешно обновлено."
fi
rm -f "$TMP_PAYLOAD"

upload_asset() {
    local file="$1"
    local name="$2"
    local mime="$3"
    local size=$(ls -lh "$file" | awk '{print $5}')

    echo "⬆️  Загрузка $name ($size)..."
    local resp=$("${CURL_CMD[@]}" --progress-bar -X POST \
        -H "Authorization: token $TOKEN" \
        -H "Content-Type: $mime" \
        -H "User-Agent: AntigravityToolkit" \
        --data-binary @"$file" \
        "https://uploads.github.com/repos/$REPO/releases/$RELEASE_ID/assets?name=$name")
    
    local asset_state=$(echo "$resp" | grep -o '"state": "[^"]*"' | head -1)
    echo "✅ Файл $name успешно загружен ($asset_state)!"
}

# Очищаем старые ассеты перед загрузкой новых
echo "🔍 Проверка и очистка старых ассетов..."
node -e '
    const cp = require("child_process");
    const token = process.argv[1];
    const proxy = process.argv[2];
    const releaseId = process.argv[3];
    const repo = process.argv[4];
    const proxyArg = proxy ? `-x ${proxy}` : "";
    try {
        const out = cp.execSync(`curl --http1.1 -s ${proxyArg} -H "Authorization: token ${token}" -H "User-Agent: AntigravityToolkit" "https://api.github.com/repos/${repo}/releases/${releaseId}/assets"`).toString();
        const assets = JSON.parse(out);
        for (const a of assets) {
            console.log(`  - Удаление устаревшего ассета ${a.name} (ID: ${a.id})...`);
            cp.execSync(`curl --http1.1 -s ${proxyArg} -X DELETE -H "Authorization: token ${token}" -H "User-Agent: AntigravityToolkit" "https://api.github.com/repos/${repo}/releases/assets/${a.id}"`);
        }
    } catch(e) {}
' "$TOKEN" "${PROXY_HOST:+http://${PROXY_HOST}:${PROXY_PORT}}" "$RELEASE_ID" "$REPO"

upload_asset "$DMG_PATH" "Antigravity-Toolkit-GUI-macOS-arm64.dmg" "application/octet-stream"
upload_asset "$ZIP_PATH" "Antigravity-Toolkit-GUI-macOS-arm64.zip" "application/zip"

echo "========================================================================"
echo "🎉 ПАКЕТЫ УСПЕШНО РАЗМЕЩЕНЫ НА GITHUB!"
echo "👉 Ссылка на релиз: https://github.com/$REPO/releases/tag/$TAG"
echo "👉 Прямая ссылка на DMG: https://github.com/$REPO/releases/download/$TAG/Antigravity-Toolkit-GUI-macOS-arm64.dmg"
echo "👉 Прямая ссылка на ZIP: https://github.com/$REPO/releases/download/$TAG/Antigravity-Toolkit-GUI-macOS-arm64.zip"
echo "========================================================================"
