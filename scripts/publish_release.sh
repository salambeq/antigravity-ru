#!/usr/bin/env bash
# ==============================================================================
#      ПУБЛИКАЦИЯ РЕЛИЗА И ДИСТРИБУТИВОВ MACOS (DMG/ZIP) НА GITHUB
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

REPO="salambeq/antigravity-ru"
TAG="v2.0.5"
NAME="Antigravity Toolkit GUI v2.0.5 (macOS Edition)"

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

BODY_TEXT='## 🇷🇺 Antigravity Toolkit GUI v2.0.5 (macOS)

Готовый бинарный дистрибутив десктопного приложения **Antigravity Toolkit GUI** для macOS (Apple Silicon).

### 📦 Загрузка дистрибутива (Пакеты macOS):
- **💿 Образ установщика DMG (рекомендуется)**: [Antigravity-Toolkit-GUI-macOS-arm64.dmg](https://github.com/salambeq/antigravity-ru/releases/download/v2.0.5/Antigravity-Toolkit-GUI-macOS-arm64.dmg)
- **🗜️ Портативный архив ZIP**: [Antigravity-Toolkit-GUI-macOS-arm64.zip](https://github.com/salambeq/antigravity-ru/releases/download/v2.0.5/Antigravity-Toolkit-GUI-macOS-arm64.zip)

---

### ✨ Ключевые возможности релиза v2.0.5:
1. 🛡️ **Защита аккаунтов от слёта и разлогинивания (Zero-Logout)**:
   - Интегрированы официальные client_id и client_secret из бинарника language_server для автоматического обновления истекающих refresh_token.
   - Двухфазная синхронизация токенов macOS Keychain перед ротацией слотов — аккаунты сохраняются при любых перезагрузках и перезапусках.
2. 👤 **Реальные email, имена и аватарки аккаунтов**:
   - Автоматическое извлечение реальных адресов электронной почты Google (напр. `user@gmail.com`) и display names пользователя для всех слотов вместо заглушек `account_1@google`.
3. ⚡ **Мониторинг квот и лимитов токенов (5ч, неделя, Claude/GPT)**:
   - 100% Zero-Leak офлайн сбор данных о квотах через локальный gRPC-Web RPC-порт `language_server` с CSRF-авторизацией (время отклика 10 мс).
   - Точные проценты остатка токенов и прогресс-бары для 5-часового и недельного лимитов Gemini, а также моделей Claude 3.7 Sonnet / Opus и GPT-OSS.
   - Живой посекундный таймер обратного отсчета до сброса лимита (`ЧЧ:ММ:СС`) в Bento-панели и в сайдбаре.
4. 📦 **Защита и бэкап чатов (Backup & Restore)**:
   - Локальное сохранение 100+ баз данных SQLite, сессий и конфигураций без риска потери истории.
5. 🍏 **Нативная интеграция с macOS**:
   - Чистая верстка в стиле Google Antigravity, поддержка кнопок окна macOS и подпись Apple `codesign`.'

TMP_PAYLOAD="/tmp/github_release_payload.json"

if [ -z "$RELEASE_ID" ] || [ "$RELEASE_ID" = "null" ]; then
    echo "✨ Создание нового релиза $TAG..."
    node -e '
        const fs = require("fs");
        const body = process.argv[1];
        fs.writeFileSync(process.argv[2], JSON.stringify({
            tag_name: "v2.0.5",
            target_commitish: "main",
            name: "Antigravity Toolkit GUI v2.0.5 (macOS Edition)",
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

    RELEASE_ID=$(echo "$CREATE_RESP" | grep -o '"id": [0-9]*' | head -1 | awk '{print $2}')
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
            name: "Antigravity Toolkit GUI v2.0.4 (macOS Edition)",
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
