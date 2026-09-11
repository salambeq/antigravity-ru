# 🇷🇺 Antigravity 2.0 — Русская локализация (Russian Localization)

Полная локализация десктопного приложения **Google Antigravity 2.0** на русский язык для всех платформ (**macOS**, **Windows**, **Linux**).

Репозиторий включает:
1. 🔄 **Автопатчер обновлений** — наложение перевода при установке или обновлении Antigravity в один клик.
2. 🇷🇺 **Глобальные правила агента** — системные инструкции для ответов и генерации кода на грамотном русском языке.
3. 🌐 **Переключатель языков** — мгновенное переключение между RU и EN версиями интерфейса.
4. 🛠 **Навык автолокализации проектов (`i18n-helper`)** — встроенный инструмент для интернационализации ваших проектов.

---

## 📋 Таблица путей к ресурсам Antigravity

| Операционная система | Стандартный путь к каталогу ресурсов (`resources`) | Бинарный файл ядра |
| :--- | :--- | :--- |
| 🍏 **macOS** | `/Applications/Antigravity.app/Contents/Resources` | `bin/language_server` |
| 🪟 **Windows** | `%LOCALAPPDATA%\Programs\Antigravity\resources` | `bin\language_server.exe` |
| 🐧 **Linux** | `/opt/Antigravity/resources` или `~/.local/share/antigravity/resources` | `bin/language_server` |

> 💡 *Если программа установлена в нестандартную директорию, вы можете задать переменную окружения:*
> - **macOS / Linux**: `export ANTIGRAVITY_RESOURCES_PATH="/ваш/путь/к/resources"`
> - **Windows (PowerShell)**: `$env:ANTIGRAVITY_RESOURCES_PATH = "C:\ваш\путь\resources"`

---

## ⚙️ Предварительные требования

Перед запуском скриптов убедитесь, что в системе установлены:
- **Python 3.8+** (для работы скриптов распаковки и замены строк);
- **Node.js и npm/npx** (требуются для работы утилиты `@electron/asar`).

---

## 📖 Подробные инструкции по каждому пункту

### 1. 🔄 Автопатчер локализации (`apply_patch`)

Скрипт автоматически:
- Создаёт резервные копии оригинальных файлов (`.orig`);
- Извлекает веб-бандл React из бинарника ядра `language_server`, переводит элементы интерфейса и упаковывает обратно;
- Корректирует структуру данных слайса памяти Go и (на macOS) переподписывает бинарник через системный Apple `codesign`;
- Распаковывает `app.asar`, переводит нативные меню, системный трей, диалоги и центр обновлений, внедряет MutationObserver для всплывающих подсказок и собирает обратно.

#### 🍏 macOS:
```bash
cd "Antigravity Localization"
chmod +x apply_patch.sh
./apply_patch.sh
```

#### 🪟 Windows (PowerShell):
```powershell
cd "Antigravity Localization"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\apply_patch.ps1
```

#### 🐧 Linux:
```bash
cd "Antigravity Localization"
chmod +x apply_patch.sh
./apply_patch.sh
```

---

### 2. 🌐 Переключатель языков в один клик (`switch_lang`)

Позволяет за секунду переключать интерфейс между русским и оригинальным английским языком без повторной сборки.

#### 🍏 macOS и 🐧 Linux:
```bash
# Включить русский интерфейс:
./switch_lang.sh ru

# Вернуть оригинальный английский интерфейс:
./switch_lang.sh en
```

#### 🪟 Windows (PowerShell):
```powershell
# Включить русский интерфейс:
.\switch_lang.ps1 -Language ru

# Вернуть оригинальный английский интерфейс:
.\switch_lang.ps1 -Language en
```
*После переключения перезапустите Antigravity (закройте окно и запустите программу заново).*

---

### 3. ⏪ Восстановление оригинального состояния (`restore_original`)

Если вы хотите полностью сбросить любые изменения и вернуться к заводской версии:

#### 🍏 macOS и 🐧 Linux:
```bash
./restore_original.sh
```

#### 🪟 Windows (PowerShell):
```powershell
.\restore_original.ps1
```

---

### 4. 🇷🇺 Глобальные правила агента на русском языке (`Rules`)

Чтобы агент Antigravity всегда общался на русском языке, соблюдал профессиональную терминологию русскоязычных разработчиков и генерировал артефакты планов (`implementation_plan.md`) и отчётов (`walkthrough.md`) на русском языке:

#### Установка глобального плагина правил:
Скопируйте плагин `russian-dev-plugin` в глобальный каталог Antigravity:

- **macOS / Linux**:
```bash
mkdir -p ~/.gemini/config/plugins/russian-dev-plugin/rules
cp rules/russian-development.md ~/.gemini/config/plugins/russian-dev-plugin/rules/
```

- **Windows (PowerShell)**:
```powershell
$target = "$env:USERPROFILE\.gemini\config\plugins\russian-dev-plugin\rules"
New-Item -ItemType Directory -Force -Path $target
Copy-Item "rules\russian-development.md" "$target\russian-development.md"
```

#### Для конкретного проекта:
Просто поместите файл `GEMINI.md` из этого репозитория в корень вашего проекта.

---

### 5. 🛠 Навык автолокализации проектов (`i18n-helper`)

Навык `i18n-helper` обучает агента Antigravity профессионально локализовать любые ваши веб- и мобильные приложения (React, Vue, Flutter, iOS, Android, Python, Go).

#### Установка навыка в Antigravity:
- **macOS / Linux**:
```bash
mkdir -p ~/.gemini/config/plugins/russian-dev-plugin/skills/i18n-helper
cp skills/i18n-helper/SKILL.md ~/.gemini/config/plugins/russian-dev-plugin/skills/i18n-helper/
```

- **Windows (PowerShell)**:
```powershell
$skillTarget = "$env:USERPROFILE\.gemini\config\plugins\russian-dev-plugin\skills\i18n-helper"
New-Item -ItemType Directory -Force -Path $skillTarget
Copy-Item "skills\i18n-helper\SKILL.md" "$skillTarget\SKILL.md"
```

#### Как использовать:
Просто напишите агенту в чате:
> *"Локализуй мой проект: найди все захардкоженные строки и подключи i18next"*
> или
> *"Подготовь файл переводов на русский язык для этого компонента"*

Агент активирует навык `i18n-helper`, найдёт текстовые литералы, создаст файлы переводов (с поддержкой русской плюрализации) и обновит компоненты.

---

## 📁 Структура репозитория

```
antigravity-ru/
├── README.md                      # Полное руководство на русском языке
├── GEMINI.md                      # Стандарты разработки для агента
├── .gitignore                     # Исключение бинарных кэшей и временных файлов
│
├── apply_patch.sh                 # Автопатчер для macOS / Linux
├── apply_patch.ps1                # Автопатчер для Windows
├── switch_lang.sh                 # Переключатель языков ru/en для macOS / Linux
├── switch_lang.ps1                # Переключатель языков ru/en для Windows
├── restore_original.sh            # Скрипт отката для macOS / Linux
├── restore_original.ps1           # Скрипт отката для Windows
│
├── patch_binary.py                # Универсальный движок патча бинарника ядра
├── patch_asar.py                  # Универсальный движок патча Electron app.asar
├── localize_frontend.py           # Словарь и алгоритм замены строк веб-бандла
│
├── rules/
│   └── russian-development.md     # Правила общения и написания кода на русском
└── skills/
    └── i18n-helper/
        └── SKILL.md               # Навык локализации пользовательских проектов
```

---

## ❓ Часто задаваемые вопросы (FAQ)

**В: Что произойдет, если Antigravity обновится через автообновление?**  
О: Приложение обновится до новой версии на английском языке. Чтобы вернуть русский язык, просто выполните `./apply_patch.sh` (или `.\apply_patch.ps1` на Windows). Патчер автоматически подстроится под новые смещения и применит перевод.

**В: Безопасно ли изменение бинарного файла на macOS?**  
О: Да. Наш скрипт переподписывает изменённый бинарник валидной локальной подписью Apple (`codesign --force --deep --sign -`), поэтому macOS не блокирует запуск приложения.

**В: Где хранятся резервные копии?**  
О: В папке ресурсов программы рядом с оригинальными файлами: `app.asar.orig` и `language_server[.exe].orig`.
