import os, sys, re, subprocess

main_js_path = '/Users/Salambek/Antigravity Localization/frontend_bundle/main.js'

with open(main_js_path, 'r', encoding='utf-8') as f:
    code = f.read()

print(f"Original length: {len(code)}")

# Comprehensive translation dictionary
# Format: (exact target string, replacement)
translations = [
    # 1. Navigation & Sidebar
    ('"New Conversation"', '"Новый чат"'),
    ('"Open Conversation History"', '"История диалогов"'),
    ('"Select Next Conversation"', '"Следующий диалог"'),
    ('"Select Previous Conversation"', '"Предыдущий диалог"'),
    ('"Scheduled Tasks"', '"Запланированные задачи"'),
    ('"Search tasks..."', '"Поиск задач..."'),
    ('"emptyMessageSingular:"scheduled task""', '"emptyMessageSingular:"запланированная задача""'),
    ('"emptyMessagePlural:"scheduled tasks""', '"emptyMessagePlural:"запланированные задачи""'),
    ('emptyMessageSingular:"scheduled task"', 'emptyMessageSingular:"запланированная задача"'),
    ('emptyMessagePlural:"scheduled tasks"', 'emptyMessagePlural:"запланированные задачи"'),
    ('"UI Plugins"', '"Плагины UI"'),
    ('"Search plugins..."', '"Поиск плагинов..."'),
    ('emptyMessageSingular:"plugin"', 'emptyMessageSingular:"плагин"'),
    ('emptyMessagePlural:"plugins"', 'emptyMessagePlural:"плагины"'),
    ('"Automations"', '"Автоматизации"'),
    ('"Search automations..."', '"Поиск автоматизаций..."'),
    ('emptyMessageSingular:"automation"', 'emptyMessageSingular:"автоматизация"'),
    ('emptyMessagePlural:"automations"', 'emptyMessagePlural:"автоматизации"'),
    ('"Search projects..."', '"Поиск проектов..."'),
    ('"Search for commands..."', '"Поиск команд..."'),
    ('"Search for conversations..."', '"Поиск диалогов..."'),
    ('"Search customizations..."', '"Поиск кастомизаций..."'),
    ('"Search MCP servers by name"', '"Поиск MCP-серверов по имени"'),
    ('"No conversations found"', '"Диалоги не найдены"'),
    ('"No step data available"', '"Нет данных шага"'),
    ('"No trajectory metadata available"', '"Нет метаданных траектории"'),
    ('"Toggle Sidebar"', '"Боковая панель"'),
    ('"Collapse Sidebar"', '"Свернуть панель"'),
    ('"Expand Sidebar"', '"Развернуть панель"'),
    ('"Open Settings"', '"Настройки"'),
    ('"Provide feedback"', '"Оставить отзыв"'),
    ('"Copy conversation markdown"', '"Скопировать диалог в Markdown"'),
    ('"Archive this conversation"', '"Архивировать диалог"'),
    ('"Find in conversation"', '"Найти в диалоге"'),
    ('"New Project"', '"Новый проект"'),
    ('"Open Folder"', '"Открыть папку"'),

    # 2. Chat Canvas & Execution Steps
    ('"Ask anything, @ to mention"', '"Спросите о чём угодно, @ для контекста"'),
    ('", / for actions"', '", / для действий"'),
    ('"Accept Step"', '"Принять шаг"'),
    ('"Reject Step"', '"Отклонить шаг"'),
    ('"Accept all"', '"Принять все"'),
    ('"Reject all"', '"Отклонить все"'),
    ('"Action Required"', '"Требуется действие"'),
    ('"Action required"', '"Требуется действие"'),
    ('"Action requires your attention"', '"Действие требует вашего внимания"'),
    ('"Thinking..."', '"Размышляет..."'),
    ('"Running command..."', '"Выполняется команда..."'),
    ('"Send Now"', '"Отправить сейчас"'),
    ('"Toggle Model Selector"', '"Выбор модели"'),
    ('"Start Voice Recording"', '"Начать запись голоса"'),
    ('"Stop Voice Recording"', '"Остановить запись голоса"'),
    ('"Toggle Voice Recording"', '"Голосовой ввод"'),
    ('"Toggle Terminal"', '"Терминал"'),
    ('"Toggle File Viewer"', '"Просмотр файлов"'),
    ('"Edit comment"', '"Редактировать комментарий"'),
    ('"Delete comment"', '"Удалить комментарий"'),
    ('"Unstage change"', '"Отменить индексацию"'),
    ('"Stage change"', '"Индексировать изменение"'),
    ('"Discard unstaged changes"', '"Сбросить неиндексированные изменения"'),

    # 3. Auxiliary Panel Tabs
    ('title:"Subagents"', 'title:"Подагенты"'),
    ('title:"Background Tasks"', 'title:"Фоновые задачи"'),
    ('title:"Artifacts"', 'title:"Артефакты"'),
    ('title:"Files Changed"', 'title:"Изменённые файлы"'),
    ('title:"Terminals"', 'title:"Терминалы"'),
    ('text-sm"},"Terminals")', 'text-sm"},"Терминалы")'),

    # 4. Settings Screens definitions
    (
        'var tXa=[{screen:"General"},{screen:"App",label:"Application"},{screen:"Appearance"},{screen:"Notifications"},{screen:"Models"},{screen:"Customizations"},{screen:"Browser"},{screen:"Developer"},{screen:"Tab"},{screen:"Editor"},{screen:"CitC Settings"},{screen:"Best of N"},{screen:"Jetski Chat"},{screen:"Labs"},{screen:"Regroup Google3 Chats"}]',
        'var tXa=[{screen:"General",label:"Общие"},{screen:"App",label:"Приложение"},{screen:"Appearance",label:"Внешний вид"},{screen:"Notifications",label:"Уведомления"},{screen:"Models",label:"Модели"},{screen:"Customizations",label:"Кастомизации"},{screen:"Browser",label:"Браузер"},{screen:"Developer",label:"Разработчик"},{screen:"Tab",label:"Подсказки Tab"},{screen:"Editor",label:"Редактор"},{screen:"CitC Settings",label:"Настройки CitC"},{screen:"Best of N",label:"Best of N"},{screen:"Jetski Chat",label:"Чат Jetski"},{screen:"Labs",label:"Эксперименты"},{screen:"Regroup Google3 Chats",label:"Группировка чатов"}]'
    ),

    # 5. Settings Sections
    ('title:"Chat Settings"', 'title:"Настройки чата"'),
    ('title:"Execution"', 'title:"Выполнение"'),
    ('title:"Terminal"', 'title:"Терминал"'),
    ('title:"Suggestions"', 'title:"Подсказки"'),
    ('title:"Default Customizations"', 'title:"Стандартные кастомизации"'),
    ('title:"Personal Customizations"', 'title:"Пользовательские кастомизации"'),
    ('title:"Customize Global Skills"', 'title:"Глобальные навыки"'),
    ('title:"Custom Agents"', 'title:"Пользовательские агенты"'),
    ('title:"MCP Servers"', 'title:"MCP-серверы"'),
    ('title:"Active Skills"', 'title:"Активные навыки"'),

    # 6. Settings Labels
    ('label:"Allow List Terminal Commands"', 'label:"Белый список команд терминала"'),
    ('label:"Deny List Terminal Commands"', 'label:"Чёрный список команд терминала"'),
    ('label:"Agent Auto-Fix Lints"', 'label:"Автоисправление ошибок линтера"'),
    ('label:"Queued Messages"', 'label:"Очередь сообщений"'),
    ('label:"Confirm Window Reload"', 'label:"Подтверждать перезагрузку окна"'),
    ('label:"Enable Demo Mode (Beta)"', 'label:"Режим демонстрации (бета)"'),
    ('label:"Explain and Fix in Current Conversation"', 'label:"Объяснять и исправлять в текущем чате"'),
    ('label:"Strict Mode"', 'label:"Строгий режим"'),
    ('label:"Agent Non-Workspace File Access"', 'label:"Доступ агента к внешним файлам"'),
    ('label:"Command Setup Script"', 'label:"Скрипт инициализации команд"'),
    ('label:"Enable Terminal Sandbox"', 'label:"Песочница терминала"'),
    ('label:"Sandbox Allow Network"', 'label:"Разрешить сеть в песочнице"'),
    ('label:"Enable Shell Integration"', 'label:"Интеграция с оболочкой"'),
    ('label:"Terminal Command Auto Execution"', 'label:"Автовыполнение команд терминала"'),
    ('label:"Agent Host Address"', 'label:"Адрес хоста агента"'),
    ('label:"Review Policy"', 'label:"Политика проверки изменений"'),
    ('label:"Enable Sounds for Agent"', 'label:"Звуковые сигналы агента"'),
    ('label:"Enable Notifications for Agent"', 'label:"Уведомления от агента"'),
    ('label:"Auto-Expand Changes Overview"', 'label:"Автораскрытие обзора изменений"'),
    ('label:"[Dev] GCP Project ID"', 'label:"[Разработка] GCP Project ID"'),
    ('label:"Conversation History"', 'label:"История диалогов"'),
    ('label:"Knowledge"', 'label:"База знаний"'),
    ('label:"Auto-Open Edited Files"', 'label:"Автоматически открывать измененные файлы"'),
    ('label:"Open Agent on Reload"', 'label:"Открывать агента при перезагрузке"'),
    ('label:"Verbose Agent Chat"', 'label:"Подробный ход мыслей агента"'),
    ('label:"Conversation Width"', 'label:"Ширина панели диалога"'),
    ('label:"Suggestions in Editor"', 'label:"Подсказки в редакторе"'),
    ('label:"Tab to Jump"', 'label:"Переход по клавише Tab"'),
    ('label:"Tab to Import"', 'label:"Импорт по клавише Tab"'),
    ('label:"Tab Speed"', 'label:"Скорость появления подсказок Tab"'),
    ('label:"Highlight After Accept"', 'label:"Подсветка после принятия"'),
    ('label:"Tab Gitignore Access"', 'label:"Доступ к файлам .gitignore"'),
    ('label:"Enable Browser Tools"', 'label:"Инструменты браузера"'),
    ('label:"Browser Javascript Execution Policy"', 'label:"Выполнение JS в браузере"'),
    ('label:"Chrome Binary Path"', 'label:"Путь к Chrome"'),
    ('label:"Browser User Profile Path"', 'label:"Путь к профилю браузера"'),
    ('label:"Browser CDP Port"', 'label:"Порт CDP браузера"'),
    ('label:"Show Selection Actions"', 'label:"Действия при выделении текста"'),
    ('label:"Include Jetski Default Customizations"', 'label:"Стандартные кастомизации"'),
    ('label:"Enable Personal Customizations"', 'label:"Пользовательские кастомизации"'),
    ('label:"Prevent Sleep"', 'label:"Предотвращать спящий режим"'),
    ('label:"Keep In Menu Bar"', 'label:"Отображать в строке меню"'),
    ('label:"Automatic Check for Updates"', 'label:"Автоматическая проверка обновлений"'),
    ('label:"Enable Remote Control"', 'label:"Удаленное управление"'),
    ('label:"Nickname"', 'label:"Отображаемое имя"'),
    ('label:"Conversation Sharing"', 'label:"Совместный доступ к чатам"'),
    ('label:"Inline Actions"', 'label:"Встроенные действия"'),

    # 7. Setting Descriptions
    ('description:"Give the agent awareness of lint errors created by its edits so it can fix them without explicit prompting."', 'description:"Позволяет агенту видеть ошибки линтера, вызванные его правками, и исправлять их без напоминаний."'),
    ('description:"Configure when follow-up messages are sent."', 'description:"Настройка отправки последующих сообщений."'),
    ('description:"Run terminal commands with sandbox restrictions."', 'description:"Запуск команд терминала в изолированной безопасной среде."'),
    ('description:"Allow sandboxed commands to make network requests."', 'description:"Разрешить командам из песочницы доступ в интернет."'),
    ('description:"Play a sound when the agent finishes generating a response."', 'description:"Звуковое оповещение по завершении генерации ответа агентом."'),
    ('description:"Display and preserve intermediate thinking steps."', 'description:"Отображать и сохранять промежуточные шаги размышлений агента."'),
    ('description:"Configure the maximum width of the conversation panel."', 'description:"Настройка максимальной ширины панели диалога."'),
    ('description:"Open the agent panel on window reload"', 'description:"Автоматически открывать панель агента при перезагрузке окна."'),
    ('description:"Open files in the editor after the agent edits them."', 'description:"Открывать файлы в редакторе после того, как агент изменит их."'),
    ('description:"Let the agent access its knowledge base."', 'description:"Разрешить агенту доступ к базе знаний."'),
    ('description:"Prevent the computer from sleeping while the app is running."', 'description:"Не переводить компьютер в спящий режим во время работы приложения."'),

    # 8. Options in Toggle Groups
    ('case 2:return"Narrow";case 3:return"Wide";default:return"Default"', 'case 2:return"Узкая";case 3:return"Широкая";default:return"По умолчанию"'),
    ('case R.MessageDeliveryStrategy.NEXT_INVOCATION:return"Send Immediately";default:return"Queue"', 'case R.MessageDeliveryStrategy.NEXT_INVOCATION:return"Отправлять сразу";default:return"В очередь"'),
    ('case R.MessageDeliveryStrategy.NEXT_INVOCATION:return"Interrupt the agent and send immediately.";default:return"Queue until after the current turn."', 'case R.MessageDeliveryStrategy.NEXT_INVOCATION:return"Прервать агента и отправить немедленно.";default:return"Поставить в очередь до завершения текущего хода."'),

    # 9. Dialog and Button Labels
    ('data-testid:"confirm-delete-sidecar"},"Delete"', 'data-testid:"confirm-delete-sidecar"},"Удалить"'),
    ('variant:"destructive",onClick:e,"data-autofocus":"true","data-testid":"confirm-delete-sidecar"},"Delete"', 'variant:"destructive",onClick:e,"data-autofocus":"true","data-testid":"confirm-delete-sidecar"},"Удалить"'),
    ('aria-label:"Settings"', 'aria-label:"Настройки"'),
    ('header:"Workspaces"', 'header:"Рабочие области"'),
    ('header:"Projects"', 'header:"Проекты"'),
]

applied = 0
for target, repl in translations:
    if target in code:
        count = code.count(target)
        code = code.replace(target, repl)
        applied += count
        print(f"✓ Replaced ({count}x): {target[:40]}...")
    else:
        print(f"✗ Not found: {target[:40]}...")

with open(main_js_path, 'w', encoding='utf-8') as f:
    f.write(code)

print(f"\nDone! Total replacements: {applied}")
print(f"New length: {len(code)}")

# Verify syntax with node -c
res = subprocess.run(['node', '-c', main_js_path], capture_output=True, text=True)
if res.returncode == 0:
    print("✓ JavaScript syntax validation PASSED!")
else:
    print("✗ Syntax Error:", res.stderr)
    sys.exit(1)
