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
    ipc_path = os.path.join(dist_dir, 'ipcHandlers.js')
    patch_file(ipc_path, [
        ("title: 'Open workspace'", "title: 'Открыть рабочую область'"),
        ("title: 'Open workspaces'", "title: 'Открыть рабочие области'")
    ])
    if os.path.exists(ipc_path):
        with open(ipc_path, 'r', encoding='utf-8') as f:
            ipc_code = f.read()
        if "accounts:get-slots" not in ipc_code:
            ipc_injection = """
    // =========================================================================
    // Antigravity Multi-Account Switcher IPC Handlers (Zero-Revocation)
    // =========================================================================
    const child_process_accounts = require("child_process");
    const path_accounts = require("path");
    const os_accounts = require("os");
    const fs_accounts = require("fs");

    const accountsDir = path_accounts.join(os_accounts.homedir(), '.gemini', 'accounts');
    const slotsDir = path_accounts.join(accountsDir, 'slots');
    const metaPath = path_accounts.join(accountsDir, 'metadata.json');
    const altMetaPath = path_accounts.join(accountsDir, 'accounts_meta.json');
    const pendingPath = path_accounts.join(accountsDir, 'pending_wizard.json');
    const jetskiTokenPath = path_accounts.join(os_accounts.homedir(), '.gemini', 'jetski-standalone-oauth-token');

    function payloadToJetskiJson(rawPayload) {
        if (!rawPayload) return '';
        try {
            if (rawPayload.startsWith('go-keyring-base64:')) {
                const b64 = rawPayload.slice(18);
                return Buffer.from(b64, 'base64').toString('utf8');
            } else if (rawPayload.trim().startsWith('{')) {
                return rawPayload.trim();
            }
        } catch {}
        return '';
    }

    function jetskiJsonToPayload(jsonStr) {
        if (!jsonStr) return '';
        try {
            const b64 = Buffer.from(jsonStr.trim(), 'utf8').toString('base64');
            return `go-keyring-base64:${b64}`;
        } catch {
            return '';
        }
    }

    function getMacKeychainToken(service = 'gemini', account = 'antigravity') {
        try {
            return child_process_accounts.execSync(`security find-generic-password -s "${service}" -a "${account}" -w`, {
                encoding: 'utf8',
                stdio: ['ignore', 'pipe', 'ignore']
            }).trim();
        } catch {
            return '';
        }
    }

    function setMacKeychainToken(rawVal, service = 'gemini', account = 'antigravity') {
        if (!rawVal) return false;
        try {
            const child = child_process_accounts.spawnSync('security', [
                'add-generic-password', '-U',
                '-s', service,
                '-a', account,
                '-w', rawVal
            ], { stdio: ['ignore', 'ignore', 'ignore'] });
            return child.status === 0;
        } catch {
            return false;
        }
    }

    function deleteMacKeychainToken(service = 'gemini', account = 'antigravity') {
        try {
            child_process_accounts.spawnSync('security', [
                'delete-generic-password',
                '-s', service,
                '-a', account
            ], { stdio: ['ignore', 'ignore', 'ignore'] });
            return true;
        } catch {
            return false;
        }
    }

    function readCurrentRawToken() {
        // 1. Проверяем файл токена ~/.gemini/jetski-standalone-oauth-token
        if (fs_accounts.existsSync(jetskiTokenPath)) {
            try {
                const content = fs_accounts.readFileSync(jetskiTokenPath, 'utf8').trim();
                if (content && content.startsWith('{')) {
                    const parsed = JSON.parse(content);
                    if (parsed.token) {
                        return jetskiJsonToPayload(content);
                    }
                }
            } catch {}
        }
        // 2. Проверяем системную связку ключей macOS Keychain
        return getMacKeychainToken('gemini', 'antigravity') || getMacKeychainToken('Antigravity', 'antigravity');
    }

    function writeRawToken(rawPayload) {
        if (!rawPayload) return false;
        // 1. Записываем в ~/.gemini/jetski-standalone-oauth-token
        const jsonStr = payloadToJetskiJson(rawPayload);
        if (jsonStr) {
            try {
                const geminiDir = path_accounts.dirname(jetskiTokenPath);
                if (!fs_accounts.existsSync(geminiDir)) {
                    fs_accounts.mkdirSync(geminiDir, { recursive: true });
                }
                fs_accounts.writeFileSync(jetskiTokenPath, jsonStr, { encoding: 'utf8', mode: 0o600 });
            } catch (e) {
                console.error('[Accounts] Failed to write jetski token:', e);
            }
        }
        // 2. Записываем в связку ключей macOS Keychain
        const keyringRaw = rawPayload.startsWith('go-keyring-base64:') ? rawPayload : jetskiJsonToPayload(rawPayload);
        setMacKeychainToken(keyringRaw, 'gemini', 'antigravity');
        setMacKeychainToken(keyringRaw, 'Antigravity', 'antigravity');
        return true;
    }

    function deleteCurrentRawToken() {
        // 1. Удаляем ~/.gemini/jetski-standalone-oauth-token
        if (fs_accounts.existsSync(jetskiTokenPath)) {
            try {
                fs_accounts.unlinkSync(jetskiTokenPath);
            } catch (e) {
                console.error('[Accounts] Failed to delete jetski token:', e);
            }
        }
        // 2. Удаляем из связки ключей
        deleteMacKeychainToken('gemini', 'antigravity');
        deleteMacKeychainToken('Antigravity', 'antigravity');
        return true;
    }

    function restartLanguageServer() {
        try {
            if (process.platform === 'darwin' || process.platform.startsWith('linux')) {
                child_process_accounts.spawnSync('pkill', ['-f', 'language_server.*--standalone'], { stdio: 'ignore' });
            }
        } catch {}
    }

    electron_1.ipcMain.handle('accounts:get-slots', async () => {
        try {
            let meta = { active_slot: 1, slots: {} };
            if (fs_accounts.existsSync(metaPath)) {
                try {
                    meta = JSON.parse(fs_accounts.readFileSync(metaPath, 'utf8'));
                } catch {}
            }

            // Если запущен мастер привязки, проверяем, появился ли новый токен
            if (fs_accounts.existsSync(pendingPath)) {
                try {
                    const pendingData = JSON.parse(fs_accounts.readFileSync(pendingPath, 'utf8'));
                    const curRaw = readCurrentRawToken();
                    if (curRaw && curRaw !== pendingData.prev_raw_payload) {
                        const targetSlot = pendingData.target_slot || ((Object.keys(meta.slots || {}).length) + 1);
                        let email = `Слот #${targetSlot}`;
                        let name = '';
                        try {
                            const b64 = curRaw.startsWith('go-keyring-base64:') ? curRaw.slice(18) : curRaw;
                            const tokObj = JSON.parse(Buffer.from(b64, 'base64').toString('utf8'));
                            if (tokObj.email) email = tokObj.email;
                            else if (tokObj.token && tokObj.token.email) email = tokObj.token.email;
                        } catch {}
                        if (!fs_accounts.existsSync(slotsDir)) {
                            fs_accounts.mkdirSync(slotsDir, { recursive: true });
                        }
                        const slotFile = path_accounts.join(slotsDir, `slot_${targetSlot}.json`);
                        const slotData = {
                            slot: targetSlot,
                            email: email,
                            name: name,
                            saved_at: Math.floor(Date.now() / 1000),
                            raw_payload: curRaw,
                            is_revoked: false
                        };
                        fs_accounts.writeFileSync(slotFile, JSON.stringify(slotData, null, 2), 'utf8');
                        meta.active_slot = targetSlot;
                        if (!meta.slots) meta.slots = {};
                        meta.slots[String(targetSlot)] = {
                            email: email,
                            name: name,
                            saved_at: slotData.saved_at,
                            is_revoked: false
                        };
                        fs_accounts.writeFileSync(metaPath, JSON.stringify(meta, null, 2), 'utf8');
                        fs_accounts.writeFileSync(altMetaPath, JSON.stringify(meta, null, 2), 'utf8');
                        fs_accounts.unlinkSync(pendingPath);
                    }
                } catch {}
            }

            const slotsList = [];
            const metaSlots = meta.slots || {};
            const activeSlot = meta.active_slot || 1;

            if (fs_accounts.existsSync(slotsDir)) {
                const files = fs_accounts.readdirSync(slotsDir);
                for (const f of files) {
                    if (f.startsWith('slot_') && f.endsWith('.json')) {
                        const num = parseInt(f.replace('slot_', '').replace('.json', ''), 10);
                        if (!isNaN(num)) {
                            try {
                                const sData = JSON.parse(fs_accounts.readFileSync(path_accounts.join(slotsDir, f), 'utf8'));
                                const needsAuth = Boolean(sData.needs_auth || sData.is_revoked || !sData.raw_payload || (metaSlots[num] && metaSlots[num].needs_auth));
                                slotsList.push({
                                    slot: num,
                                    email: sData.email || metaSlots[num]?.email || `Слот #${num}`,
                                    name: sData.name || metaSlots[num]?.name || '',
                                    is_active: (num === activeSlot),
                                    is_revoked: Boolean(sData.is_revoked),
                                    needs_auth: needsAuth
                                });
                            } catch {}
                        }
                    }
                }
            }

            slotsList.sort((a, b) => a.slot - b.slot);

            let pendingWizard = null;
            if (fs_accounts.existsSync(pendingPath)) {
                try {
                    pendingWizard = JSON.parse(fs_accounts.readFileSync(pendingPath, 'utf8'));
                } catch {}
            }

            return {
                active_slot: activeSlot,
                slots: slotsList,
                pending_wizard: pendingWizard
            };
        } catch (err) {
            return { active_slot: 1, slots: [], error: String(err) };
        }
    });

    electron_1.ipcMain.handle('accounts:switch-slot', async (_event, targetSlot) => {
        try {
            const slotNum = parseInt(targetSlot, 10);
            if (isNaN(slotNum) || slotNum < 1) {
                return { success: false, error: 'Неверный номер слота' };
            }

            const slotFile = path_accounts.join(slotsDir, `slot_${slotNum}.json`);
            if (!fs_accounts.existsSync(slotFile)) {
                return { success: false, error: `Слот #${slotNum} не существует` };
            }

            // 1. Бэкап текущего токена в активный слот
            let curMeta = { active_slot: 1, slots: {} };
            if (fs_accounts.existsSync(metaPath)) {
                try { curMeta = JSON.parse(fs_accounts.readFileSync(metaPath, 'utf8')); } catch {}
            }
            const currentActive = curMeta.active_slot || 1;
            const curRaw = readCurrentRawToken();
            if (curRaw) {
                const curSlotFile = path_accounts.join(slotsDir, `slot_${currentActive}.json`);
                if (fs_accounts.existsSync(curSlotFile)) {
                    try {
                        const curData = JSON.parse(fs_accounts.readFileSync(curSlotFile, 'utf8'));
                        curData.raw_payload = curRaw;
                        curData.saved_at = Math.floor(Date.now() / 1000);
                        fs_accounts.writeFileSync(curSlotFile, JSON.stringify(curData, null, 2), 'utf8');
                    } catch {}
                }
            }

            // 2. Читаем токен целевого слота
            const targetData = JSON.parse(fs_accounts.readFileSync(slotFile, 'utf8'));
            const targetRaw = targetData.raw_payload;
            if (!targetRaw) {
                return { success: false, error: `В слоте #${slotNum} отсутствуют данные токена` };
            }

            // 3. Записываем в jetski-токен и Keychain
            writeRawToken(targetRaw);

            // 4. Обновляем метаданные
            curMeta.active_slot = slotNum;
            if (!curMeta.slots) curMeta.slots = {};
            curMeta.slots[String(slotNum)] = {
                email: targetData.email || `Слот #${slotNum}`,
                name: targetData.name || '',
                saved_at: Math.floor(Date.now() / 1000),
                is_revoked: false
            };
            fs_accounts.writeFileSync(metaPath, JSON.stringify(curMeta, null, 2), 'utf8');
            fs_accounts.writeFileSync(altMetaPath, JSON.stringify(curMeta, null, 2), 'utf8');

            // 5. Перезапускаем языковой сервер
            restartLanguageServer();

            return { success: true, email: targetData.email, slot: slotNum };
        } catch (err) {
            return { success: false, error: String(err) };
        }
    });

    electron_1.ipcMain.handle('accounts:prepare-add', async (_event, targetSlot) => {
        try {
            const slotNum = parseInt(targetSlot, 10);
            let curMeta = { active_slot: 1, slots: {} };
            if (fs_accounts.existsSync(metaPath)) {
                try { curMeta = JSON.parse(fs_accounts.readFileSync(metaPath, 'utf8')); } catch {}
            }
            const currentActive = curMeta.active_slot || 1;
            const curRaw = readCurrentRawToken();

            // Сохраняем снимок перед входом в pending_wizard.json
            const pendingData = {
                target_slot: slotNum,
                prev_active_slot: currentActive,
                prev_raw_payload: curRaw,
                started_at: Math.floor(Date.now() / 1000)
            };
            fs_accounts.writeFileSync(pendingPath, JSON.stringify(pendingData, null, 2), 'utf8');

            // Сохраняем сессию текущего слота
            if (curRaw) {
                const curSlotFile = path_accounts.join(slotsDir, `slot_${currentActive}.json`);
                if (fs_accounts.existsSync(curSlotFile)) {
                    try {
                        const curData = JSON.parse(fs_accounts.readFileSync(curSlotFile, 'utf8'));
                        curData.raw_payload = curRaw;
                        curData.saved_at = Math.floor(Date.now() / 1000);
                        fs_accounts.writeFileSync(curSlotFile, JSON.stringify(curData, null, 2), 'utf8');
                    } catch {}
                }
            }

            // Очищаем токен из jetski-файла и Keychain для чистого входа
            deleteCurrentRawToken();

            // Перезапускаем языковой сервер
            restartLanguageServer();

            return { success: true, target_slot: slotNum };
        } catch (err) {
            return { success: false, error: String(err) };
        }
    });

    electron_1.ipcMain.handle('accounts:cancel-add', async () => {
        try {
            if (!fs_accounts.existsSync(pendingPath)) {
                return { success: false, error: 'Мастер добавления не запущен' };
            }
            const pendingData = JSON.parse(fs_accounts.readFileSync(pendingPath, 'utf8'));
            const prevRaw = pendingData.prev_raw_payload;
            if (prevRaw) {
                writeRawToken(prevRaw);
            }
            try { fs_accounts.unlinkSync(pendingPath); } catch {}
            restartLanguageServer();
            return { success: true };
        } catch (err) {
            return { success: false, error: String(err) };
        }
    });

    electron_1.ipcMain.handle('accounts:delete-slot', async (_event, targetSlot) => {
        try {
            const slotNum = parseInt(targetSlot, 10);
            let curMeta = { active_slot: 1, slots: {} };
            if (fs_accounts.existsSync(metaPath)) {
                try { curMeta = JSON.parse(fs_accounts.readFileSync(metaPath, 'utf8')); } catch {}
            }
            if (curMeta.active_slot === slotNum) {
                return { success: false, error: 'Нельзя удалить активный слот' };
            }
            const slotFile = path_accounts.join(slotsDir, `slot_${slotNum}.json`);
            if (fs_accounts.existsSync(slotFile)) {
                try { fs_accounts.unlinkSync(slotFile); } catch {}
            }
            if (curMeta.slots && curMeta.slots[String(slotNum)]) {
                delete curMeta.slots[String(slotNum)];
                fs_accounts.writeFileSync(metaPath, JSON.stringify(curMeta, null, 2), 'utf8');
                fs_accounts.writeFileSync(altMetaPath, JSON.stringify(curMeta, null, 2), 'utf8');
            }
            return { success: true, slot: slotNum };
        } catch (err) {
            return { success: false, error: String(err) };
        }
    });
}
"""
            last_brace_idx = ipc_code.rfind('}')
            if last_brace_idx != -1:
                new_ipc = ipc_code[:last_brace_idx] + ipc_injection
                with open(ipc_path, 'w', encoding='utf-8') as f:
                    f.write(new_ipc)
                print("✓ Added accounts IPC handlers to ipcHandlers.js")

    # 6. preload.js runtime bridge
    preload_path = os.path.join(dist_dir, 'preload.js')
    if os.path.exists(preload_path):
        with open(preload_path, 'r', encoding='utf-8') as f:
            code = f.read()
        if "antigravityAccounts" not in code:
            acc_preload = """
const accountsAPI = {
    getSlots: () => electron_1.ipcRenderer.invoke('accounts:get-slots'),
    switchSlot: (slotNum) => electron_1.ipcRenderer.invoke('accounts:switch-slot', slotNum),
    prepareAdd: (slotNum) => electron_1.ipcRenderer.invoke('accounts:prepare-add', slotNum),
    cancelAdd: () => electron_1.ipcRenderer.invoke('accounts:cancel-add'),
    deleteSlot: (slotNum) => electron_1.ipcRenderer.invoke('accounts:delete-slot', slotNum),
    reloadWindow: () => window.location.reload(),
};
electron_1.contextBridge.exposeInMainWorld('antigravityAccounts', accountsAPI);
"""
            # Insert before '// Antigravity 2.0 Russian' or at end
            if "// Antigravity 2.0 Russian" in code:
                code = code.replace("// Antigravity 2.0 Russian", acc_preload + "\n// Antigravity 2.0 Russian")
            else:
                code += acc_preload
            with open(preload_path, 'w', encoding='utf-8') as f:
                f.write(code)
            print("✓ Added antigravityAccounts bridge to preload.js")

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
