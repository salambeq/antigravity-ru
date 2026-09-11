import os, sys, re

def find_app_resources():
    env_path = os.environ.get("ANTIGRAVITY_RESOURCES_PATH")
    if env_path and os.path.isdir(env_path):
        return env_path

    if sys.platform == 'darwin':
        paths = ["/Applications/Antigravity.app/Contents/Resources"]
    elif sys.platform.startswith('linux'):
        paths = [
            "/opt/Antigravity/resources",
            "/usr/lib/antigravity/resources",
            os.path.expanduser("~/.local/share/antigravity/resources")
        ]
    elif sys.platform == 'win32':
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        paths = [
            os.path.join(local_app, "Programs", "Antigravity", "resources"),
            os.path.join(prog_files, "Antigravity", "resources")
        ]
    else:
        paths = []

    for p in paths:
        if os.path.isdir(p):
            return p
    return paths[0] if paths else None

def patch_file(path, replacements):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    modified = False
    for target, repl in replacements:
        if target in content:
            content = content.replace(target, repl)
            modified = True
        else:
            # Already patched or slight variance
            pass
    
    if modified:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Patched {os.path.basename(path)}")
    return True

def patch_asar_dir(dist_dir):
    # 1. menu.js
    patch_file(os.path.join(dist_dir, 'menu.js'), [
        ("label: 'New Window'", "label: 'Новое окно'"),
        ("label: 'Docs'", "label: 'Документация'"),
        ("item.label === submenuLabel", "item.label === submenuLabel || (submenuLabel === 'File' && item.label === 'Файл') || (submenuLabel === 'Help' && (item.label === 'Справка' || item.label === 'Помощь'))")
    ])

    # 2. tray.js
    patch_file(os.path.join(dist_dir, 'tray.js'), [
        (
            "(count > 0 ? `${count}` : 'No') +\n                    ' agent' +\n                    (count === 1 ? '' : 's') +\n                    ' running';",
            "count === 0 ? 'Нет активных агентов' : count === 1 ? '1 активный агент' : `${count} активных агентов`;"
        )
    ])

    # 3. updater.js
    patch_file(os.path.join(dist_dir, 'updater.js'), [
        ('MenuUpdateStep["CheckForUpdates"] = "Check for Updates";', 'MenuUpdateStep["CheckForUpdates"] = "Проверить обновления";'),
        ('MenuUpdateStep["CheckingForUpdates"] = "Checking for Updates...";', 'MenuUpdateStep["CheckingForUpdates"] = "Проверка обновлений...";'),
        ('MenuUpdateStep["DownloadingUpdate"] = "Downloading Update...";', 'MenuUpdateStep["DownloadingUpdate"] = "Загрузка обновления...";'),
        ('MenuUpdateStep["RestartToUpdate"] = "Restart to Update";', 'MenuUpdateStep["RestartToUpdate"] = "Перезапустить для обновления";'),
        ("title: 'Check for Updates',\n                message: 'No updates available',", "title: 'Проверка обновлений',\n                message: 'У вас установлена последняя версия',")
    ])

    # 4. main.js
    patch_file(os.path.join(dist_dir, 'main.js'), [
        ("label: 'New Window'", "label: 'Новое окно'"),
        ("label: 'No agents running'", "label: 'Нет активных агентов'"),
        ("label: `Open ${electron_1.app.getName()}`", "label: `Открыть ${electron_1.app.getName()}`"),
        ("label: 'Quit'", "label: 'Выйти'"),
        ("buttons: ['Cancel', 'Quit'],\n        defaultId: 1,\n        cancelId: 0,\n        title: 'Confirm Quit',\n        message: 'Are you sure you want to quit?',\n        detail: 'There may be agents or background tasks running.',",
         "buttons: ['Отмена', 'Выйти'],\n        defaultId: 1,\n        cancelId: 0,\n        title: 'Подтверждение выхода',\n        message: 'Вы уверены, что хотите выйти?',\n        detail: 'Возможно, есть активные агенты или выполняются фоновые задачи.',")
    ])

    # 5. ipcHandlers.js
    patch_file(os.path.join(dist_dir, 'ipcHandlers.js'), [
        ("title: 'Open workspace'", "title: 'Открыть рабочую область'"),
        ("title: 'Open workspaces'", "title: 'Открыть рабочие области'")
    ])

    # 6. preload.js runtime bridge
    preload_path = os.path.join(dist_dir, 'preload.js')
    if os.path.exists(preload_path):
        with open(preload_path, 'r', encoding='utf-8') as f:
            code = f.read()
        if "Antigravity 2.0 Russian Localization Runtime Bridge" not in code:
            runtime_bridge = """
// Antigravity 2.0 Russian Localization Runtime Bridge
(() => {
    const i18nMap = new Map([
        ["New Conversation", "Новый чат"],
        ["Scheduled Tasks", "Запланированные задачи"],
        ["UI Plugins", "Плагины UI"],
        ["Automations", "Автоматизации"],
        ["Settings", "Настройки"],
        ["General", "Общие"],
        ["Appearance", "Внешний вид"],
        ["Application", "Приложение"],
        ["Notifications", "Уведомления"],
        ["Models", "Модели"],
        ["Customizations", "Кастомизации"],
        ["Browser", "Браузер"],
        ["Developer", "Разработчик"],
        ["Editor", "Редактор"],
        ["Projects", "Проекты"],
        ["Workspaces", "Рабочие области"],
        ["Subagents", "Подагенты"],
        ["Background Tasks", "Фоновые задачи"],
        ["Artifacts", "Артефакты"],
        ["Files Changed", "Изменённые файлы"],
        ["Terminals", "Терминалы"],
        ["Terminal", "Терминал"],
        ["Accept Step", "Принять шаг"],
        ["Reject Step", "Отклонить шаг"],
        ["Accept all", "Принять все"],
        ["Reject all", "Отклонить все"],
        ["Action Required", "Требуется действие"],
        ["Action required", "Требуется действие"],
        ["Action requires your attention", "Действие требует вашего внимания"],
        ["Thinking...", "Размышляет..."],
        ["Running command...", "Выполняется команда..."],
        ["Send Now", "Отправить сейчас"],
        ["Delete", "Удалить"],
        ["Cancel", "Отмена"],
        ["Save", "Сохранить"],
        ["Close", "Закрыть"],
        ["Done", "Готово"],
        ["Confirm", "Подтвердить"],
        ["Retry", "Повторить"],
        ["Copy", "Копировать"],
        ["Edit", "Редактировать"],
        ["Provide feedback", "Оставить отзыв"],
        ["Copy conversation markdown", "Скопировать диалог в Markdown"],
        ["Archive this conversation", "Архивировать диалог"],
        ["Find in conversation", "Найти в диалоге"],
        ["Open Conversation History", "История диалогов"],
        ["Toggle Sidebar", "Боковая панель"],
        ["Toggle Terminal", "Терминал"],
        ["Toggle File Viewer", "Просмотр файлов"],
        ["Toggle Model Selector", "Выбор модели"],
        ["Start Voice Recording", "Начать запись голоса"],
        ["Stop Voice Recording", "Остановить запись голоса"],
        ["Toggle Voice Recording", "Голосовой ввод"],
        ["No conversations found", "Диалоги не найдены"],
        ["No step data available", "Нет данных шага"],
        ["No trajectory metadata available", "Нет метаданных траектории"],
        ["Ask anything, @ to mention, / for actions", "Спросите о чём угодно, @ для контекста, / для действий"],
        ["Ask anything, @ to mention", "Спросите о чём угодно, @ для контекста"],
        ["Search tasks...", "Поиск задач..."],
        ["Search plugins...", "Поиск плагинов..."],
        ["Search automations...", "Поиск автоматизаций..."],
        ["Search projects...", "Поиск проектов..."],
        ["Search for commands...", "Поиск команд..."],
        ["Search for conversations...", "Поиск диалогов..."],
        ["Search customizations...", "Поиск кастомизаций..."],
        ["Search MCP servers by name", "Поиск MCP-серверов по имени"],
        ["Default Customizations", "Стандартные кастомизации"],
        ["Personal Customizations", "Пользовательские кастомизации"],
        ["Customize Global Skills", "Глобальные навыки"],
        ["Custom Agents", "Пользовательские агенты"],
        ["MCP Servers", "MCP-серверы"],
        ["Active Skills", "Активные навыки"]
    ]);

    const ignoredTags = new Set(["SCRIPT", "STYLE", "PRE", "CODE", "TEXTAREA"]);

    function translateText(str) {
        if (!str) return null;
        const trimmed = str.trim();
        const translation = i18nMap.get(trimmed);
        if (translation) return str.replace(trimmed, translation);
        return null;
    }

    function translateNode(node) {
        if (!node) return;
        if (node.nodeType === 3) {
            if (node.parentNode && ignoredTags.has(node.parentNode.tagName)) return;
            const translated = translateText(node.nodeValue);
            if (translated && translated !== node.nodeValue) {
                node.nodeValue = translated;
            }
        } else if (node.nodeType === 1) {
            if (ignoredTags.has(node.tagName)) return;
            if (node.hasAttribute && node.hasAttribute("placeholder")) {
                const ph = node.getAttribute("placeholder");
                const translated = translateText(ph);
                if (translated) node.setAttribute("placeholder", translated);
            }
            if (node.hasAttribute && node.hasAttribute("title")) {
                const title = node.getAttribute("title");
                const translated = translateText(title);
                if (translated) node.setAttribute("title", translated);
            }
            if (node.hasAttribute && node.hasAttribute("aria-label")) {
                const aria = node.getAttribute("aria-label");
                const translated = translateText(aria);
                if (translated) node.setAttribute("aria-label", translated);
            }
            for (let i = 0; i < node.childNodes.length; i++) {
                translateNode(node.childNodes[i]);
            }
        }
    }

    function initObserver() {
        if (!document.body) {
            setTimeout(initObserver, 50);
            return;
        }
        translateNode(document.body);
        const observer = new MutationObserver((mutations) => {
            for (let i = 0; i < mutations.length; i++) {
                const m = mutations[i];
                if (m.type === "childList") {
                    for (let j = 0; j < m.addedNodes.length; j++) {
                        translateNode(m.addedNodes[j]);
                    }
                } else if (m.type === "characterData") {
                    translateNode(m.target);
                }
            }
        });
        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    }

    if (typeof window !== "undefined") {
        window.addEventListener("DOMContentLoaded", initObserver);
    }
})();
"""
            with open(preload_path, 'a', encoding='utf-8') as f:
                f.write(runtime_bridge)
            print("✓ Added runtime bridge to preload.js")

if __name__ == '__main__':
    dist_dir = sys.argv[1] if len(sys.argv) > 1 else None
    if not dist_dir:
        res = find_app_resources()
        if res:
            dist_dir = os.path.join(res, "app.asar.unpacked", "dist")
    if dist_dir and os.path.exists(dist_dir):
        patch_asar_dir(dist_dir)
    else:
        print(f"Usage: python3 patch_asar.py <path_to_extracted_asar/dist>")
