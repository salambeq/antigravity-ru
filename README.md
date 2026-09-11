# 🇷🇺 Antigravity Toolkit & Русская локализация (v2.0 RU)

Комплексный инструмент для **Google Antigravity 2.0**, **Antigravity IDE**, **Antigravity CLI (`agy`)** и **расширения VS Code**:
1. 🔓 **Полное снятие региональных ограничений (Region Lock Bypass)** — работа без VPN и без смены региона Google-аккаунта (`hasValidAuth=true`, `isGoogleInternal=true`, `agy eligibility bypass`).
2. 🇷🇺 **Полная русская локализация интерфейса и ядра** — перевод всех веб-экранов, боковых панелей, настроек, диалогов, системного трея и меню.
3. ⚡ **Удобный интерактивный терминал (TUI/CLI)** — единый центр управления со статусом всех установленных компонентов в реальном времени.
4. 🌐 **Мгновенный переключатель языков (RU ↔ EN)** — переключение за одну секунду без повторной сборки.
5. ⏪ **Безопасный откат к оригиналу (Restore)** — автоматические бэкапы (`.orig` / `.agybak`) и восстановление до заводского состояния в один клик.
6. 🛠 **Глобальные правила агента и навык автолокализации (`i18n-helper`)** — системные промпты по стандартам разработки на русском языке.

---

## 🖥 Интерактивный терминальный интерфейс

В проект включена русскоязычная консольная утилита с красивым псевдографическим меню, автоопределением установленных программ и диагностикой:

```
  ╔═══════════════════════════════════════════════╗
  ║  Antigravity Toolkit (v2.0 RU)         v1.3.6 ║
  ║  Region bypass & Russian localization         ║
  ║  Clean • No keys • No telemetry               ║
  ╟───────────────────────────────────────────────╢
  ║  Telegram    t.me/avencoresyt                 ║
  ║  YouTube     youtube.com/@avencores           ║
  ╚═══════════════════════════════════════════════╝

  ─ ДИАГНОСТИКА И СТАТУС КОМПОНЕНТОВ ──────────────
  ● Antigravity 2.0 (Десктопное приложение):
      Путь:              /Applications/Antigravity.app/Contents/resources/bin/language_server
      Версия:            2.12.2
      Регион (Auth):     ✅ РАЗБЛОКИРОВАН (hasValidAuth=true)
      Интерфейс:         🇷🇺 РУССКИЙ ЯЗЫК (Локализован)

  ● Antigravity IDE (Редактор на базе VS Code):
      Путь:              /Applications/Antigravity IDE.app/Contents/Resources/app/out/main.js
      Версия:            2.5.5
      Регион:            ✅ РАЗБЛОКИРОВАН (isGoogleInternal=true)

  ● Antigravity CLI (Консольная утилита agy):
      Путь:              /Users/.../.gemini/bin/agy
      Регион:            ✅ РАЗБЛОКИРОВАН (bypass eligibility)

  ● Расширение для VS Code (google.google-antigravity):
      Extension JS:      ~/.vscode/extensions/google.google-antigravity-1.2.0/extension.js
      Патч JS:           ✅ Применен
      Бинарник agy:      ~/.gemini/bin/agy
      Патч agy:          ✅ Разблокирован

  ─ ГЛАВНОЕ МЕНЮ ДЕЙСТВИЙ ─────────────────────────
  [1]  ⚡ Всё в один клик  Разблокировать регион + Полная русская локализация + Правила
  [2]  🇷🇺 Локализация интерфейса  Применить русский перевод к Antigravity 2.0
  [3]  🔓 Снять региональные ограничения  Разблокировать Antigravity 2.0, IDE, CLI, VS Code
  [4]  🌐 Переключить язык  Мгновенное переключение RU <-> EN без пересборки
  [5]  ⏪ Восстановить оригиналы  Безопасный откат всех патчей к заводскому состоянию
  [6]  🛠 Установить правила и навыки  Русские стандарты разработки и навык i18n
  [7]  🎯 Выборочные патчи  Индивидуальное управление компонентами (IDE, CLI и т.д.)
  [8]  🔍 Подробная диагностика  Проверка подписей, прав, контрольных сумм и модулей

  [0]  Выход            Завершить работу с утилитой
```

---

## 🚀 Быстрый запуск утилиты

### 🍏 macOS:
```bash
git clone https://github.com/salambeq/antigravity-ru.git
cd antigravity-ru
./antigravity-tool
# или: python3 main.py
```

### 🪟 Windows:
- В командной строке (`cmd`):
```cmd
git clone https://github.com/salambeq/antigravity-ru.git
cd antigravity-ru
antigravity-tool.bat
```
- Либо в PowerShell:
```powershell
git clone https://github.com/salambeq/antigravity-ru.git
cd antigravity-ru
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\antigravity-tool.ps1
```

### 🐧 Linux:
```bash
git clone https://github.com/salambeq/antigravity-ru.git
cd antigravity-ru
chmod +x antigravity-tool
./antigravity-tool
```

---

## ⚙️ Неинтерактивные флаги командной строки (CLI)

Для автоматизации или вызова из скриптов поддерживаются прямые аргументы:

| Флаг | Описание действия |
| :--- | :--- |
| `python3 main.py --all` (`-a`) | **Всё в один клик**: разблокировка региона, русская локализация, установка правил |
| `python3 main.py --localize` (`-l`) | Применить только русскую локализацию интерфейса |
| `python3 main.py --unlock` (`-u`) | Снять региональные ограничения со всех найденных компонентов |
| `python3 main.py --switch ru` (`-s ru`) | Мгновенно включить русский интерфейс |
| `python3 main.py --switch en` (`-s en`) | Мгновенно вернуть оригинальный английский интерфейс |
| `python3 main.py --restore` (`-r`) | Восстановить все оригинальные файлы из бэкапов |
| `python3 main.py --diagnostics` (`-d`) | Запустить полную диагностику системы и целостности файлов |

---

## 📋 Таблица путей к компонентам Antigravity

| Операционная система | Каталог ресурсов Antigravity 2.0 (`resources`) | Бинарный файл ядра | Antigravity IDE |
| :--- | :--- | :--- | :--- |
| 🍏 **macOS** | `/Applications/Antigravity.app/Contents/Resources` | `bin/language_server` | `/Applications/Antigravity IDE.app` |
| 🪟 **Windows** | `%LOCALAPPDATA%\Programs\Antigravity\resources` | `bin\language_server.exe` | `%LOCALAPPDATA%\Programs\Antigravity IDE` |
| 🐧 **Linux** | `/opt/Antigravity/resources` или `~/.local/share/antigravity/resources` | `bin/language_server` | `/usr/share/antigravity-ide` |

> 💡 *Если программа установлена в нестандартную папку, вы можете задать переменную окружения:*
> - **macOS / Linux**: `export ANTIGRAVITY_RESOURCES_PATH="/путь/к/resources"`
> - **Windows (PowerShell)**: `$env:ANTIGRAVITY_RESOURCES_PATH = "C:\путь\к\resources"`

---

## 🔬 Технические детали реализации

### 1. Снятие региональных ограничений (Region Lock Bypass)
- **Antigravity 2.0 (language_server)**:
  - Патч `MANAGER_GATE` в секции машинного кода `__TEXT`.
  - Для **arm64**: `\x03\x20\x40\x39` (чтение флага авторизации) заменяется на `\x23\x00\x80\x52\x03\x20\x00\x39` (`mov w3, #1; strb w3, [x0, #8]`).
  - Для **x86_64**: заменяется условный переход на безусловный флаг `\xc6\x40\x08\x01\x90\x90` (`mov byte [rax+8], 1; nop; nop`).
  - Принудительно устанавливает `hasValidAuth = true`, пропуская проверку региона Google Account.
- **Antigravity IDE**:
  - Патч `main.js` (`isGoogleInternal` заменяется на `true`), разблокируя функции Gemini 2.5/Pro без региональных проверок.
- **Antigravity CLI (`agy`)**:
  - Патч `CLI_GATE` машинного кода утилиты `agy` (`checkEligibility`), разрешающий выполнение задач без блокировок.
- **VS Code Extension**:
  - Патч `extension.js` и бинарника `~/.gemini/bin/agy`.

### 2. Русская локализация ядра и интерфейса
- **Ядро (`language_server`)**:
  - В бинарнике Go в секции `__DATA.__noptrdata` находится вшитый ZIP-архив с веб-интерфейсом React.
  - Патчер распаковывает и заменяет строки в `main.js`, пересобирает ZIP с максимальным сжатием (Deflate level 9) так, чтобы размер нового архива не превышал исходный.
  - Находит и обновляет Go-структуру слайса `{ ptr, len, cap }` в секции данных.
- **Оболочка Electron (`app.asar`)**:
  - Распаковывает `app.asar`, патчит нативные меню (`menu.js`), системный трей (`tray.js`), диалоговые окна (`main.js`), обработчики IPC (`ipcHandlers.js`) и центр обновлений (`updater.js`).
  - Внедряет в `preload.js` легковесный runtime-мост (`MutationObserver`), динамически переводящий динамические всплывающие подсказки (tooltips, placeholders, aria-labels).
  - Упаковывает `app.asar` с сохранением распакованных модулей (`--unpack "**/node_modules/chrome-devtools-mcp/**"`).
- **Apple Codesign (macOS)**:
  - Автоматически удаляет флаги защиты (`chflags nouchg`) и переподписывает измененные бинарники и бандлы через `codesign --force --deep --sign -`, исключая появление ошибки *«Приложение повреждено»*.

---

## 🛠 Глобальные правила агента и навык i18n

### Русские стандарты разработки (`Rules`)
Устанавливаются автоматически при выборе пункта `[6]` или `[1]`:
- Файл `rules/russian-development.md` копируется в `~/.gemini/config/plugins/russian-dev-plugin/rules/`.
- Агент всегда отвечает на грамотном техническом русском языке, использует общепринятые термины («коммит», «пулреквест», «слияние», «точка останова») и составляет планы `implementation_plan.md` и отчеты `walkthrough.md` на русском языке.

### Навык автолокализации проектов (`i18n-helper`)
- Копируется в `~/.gemini/config/plugins/russian-dev-plugin/skills/i18n-helper/`.
- Позволяет агенту автоматически находить захардкоженные строки в любом вашем проекте (React, Vue, Flutter, iOS, Python), настраивать библиотеки локализации (i18next, vue-i18n, intl) и генерировать переводы с русской плюрализацией.

---

## 📁 Структура репозитория

```
antigravity-ru/
├── antigravity-tool               # Запуск утилиты для macOS / Linux
├── antigravity-tool.bat           # Запуск утилиты для Windows (cmd)
├── antigravity-tool.ps1           # Запуск утилиты для Windows (PowerShell)
├── main.py                        # Единый центр управления и интерфейс терминала
│
├── patcher/                       # Модули патчера и локализации
│   ├── localization.py            # Движок локализации и переключения RU <-> EN
│   ├── patcher_binary_worker.py   # Модификация language_server и Go-слайса
│   ├── patcher_asar_worker.py     # Модификация и перепаковка app.asar
│   ├── cli.py                     # Консольные диалоги и подсказки
│   ├── constants.py               # Системные константы и ANSI-цвета
│   ├── manager/                   # Патчи Antigravity 2.0 (language_server)
│   ├── ide/                       # Патчи Antigravity IDE (main.js)
│   ├── agy/                       # Патчи Antigravity CLI (agy)
│   ├── vscode/                    # Патчи расширения VS Code
│   └── utils/                     # Консоль, права, файлы, атомарная замена
│
├── frontend_bundle/               # Подготовленный локализованный веб-бандл React
├── rules/
│   └── russian-development.md     # Стандарты общения и разработки на русском языке
├── skills/
│   └── i18n-helper/
│       └── SKILL.md               # Навык локализации пользовательских проектов
├── GEMINI.md                      # Инструкции проекта для AI-ассистента
└── README.md                      # Документация репозитория
```

---

## ❓ Часто задаваемые вопросы (FAQ)

**В: Слетают ли патчи после официального обновления Antigravity?**  
О: При автоматическом обновлении программа загружает свежие бинарники от Google. Чтобы восстановить русский язык и снять ограничения, просто снова запустите `./antigravity-tool` и выберите пункт `[1]`. Патчер автоматически найдет новые смещения и применит изменения.

**В: Можно ли вернуть оригинальный английский язык без переустановки?**  
О: Да. Выберите пункт `[4]` (Переключить язык) -> `[2]` (English) или выполните команду `python3 main.py --switch en`. Переключение занимает меньше 1 секунды.

**В: Безопасна ли модификация файлов на macOS?**  
О: Абсолютно. Скрипт переподписывает все измененные исполняемые файлы и бандлы Apple `codesign`, поэтому macOS Gatekeeper не блокирует запуск приложения.

**В: Как полностью удалить все патчи?**  
О: Выберите пункт `[5]` (Восстановить оригиналы) или выполните `python3 main.py --restore`. Все файлы будут возвращены к исходному заводскому состоянию из созданных бэкапов (`.orig` / `.agybak`).

---

## 📜 Лицензия и благодарности

- Патчер снятия региональных ограничений основан на наработках проекта [Open Antigravity Patcher](https://github.com/AvenCores/open-antigravity-patcher) от **AvenCores** (лицензия GPL-3.0).
- Русская локализация, runtime-мост Electron, Go-модуль слайса и навык `i18n-helper` разработаны специально для проекта **antigravity-ru**.
