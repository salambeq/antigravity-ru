const { app, BrowserWindow, ipcMain, shell, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, execFile } = require('child_process');

let mainWindow = null;
let autoRotateProcess = null;
let tray = null;
let isQuitting = false;
let cachedAllSlotsQuota = null;
let backgroundSyncTimer = null;

function resolvePythonPaths() {
  const root = app.getAppPath();
  const candidates = [
    path.join(root, 'main.py'),
    path.join(root, '..', 'main.py'),
    path.resolve(__dirname, '..', 'main.py'),
    path.join(process.resourcesPath || '', 'app', 'main.py'),
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) {
      return { rootDir: path.dirname(c), mainPy: c };
    }
  }
  return { rootDir: root, mainPy: path.join(root, 'main.py') };
}

function resolvePythonBin() {
  if (process.env.PYTHON && fs.existsSync(process.env.PYTHON)) {
    return process.env.PYTHON;
  }
  const candidates = [
    '/opt/homebrew/bin/python3',
    '/usr/local/bin/python3',
    '/usr/bin/python3',
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  return 'python3';
}

const { rootDir: ROOT_DIR, mainPy: MAIN_PY } = resolvePythonPaths();
const PYTHON_BIN = resolvePythonBin();
const DEFAULT_ENV = {
  ...process.env,
  PATH: `/opt/homebrew/bin:/usr/local/bin:${process.env.PATH || '/usr/bin:/bin:/usr/sbin:/sbin'}`
};

console.log('[Antigravity GUI] ROOT_DIR:', ROOT_DIR);
console.log('[Antigravity GUI] MAIN_PY:', MAIN_PY);
console.log('[Antigravity GUI] PYTHON_BIN:', PYTHON_BIN);

function stripAnsi(text) {
  return text.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1260,
    height: 840,
    minWidth: 1000,
    minHeight: 680,
    backgroundColor: '#0a0b0f',
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 18, y: 18 },
    icon: path.join(__dirname, 'icon.png'),
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      return false;
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (autoRotateProcess) {
      autoRotateProcess.kill();
      autoRotateProcess = null;
    }
  });
}

function createTray() {
  if (tray) return;

  const iconPath = path.join(__dirname, 'icon.png');
  let icon = nativeImage.createEmpty();
  if (fs.existsSync(iconPath)) {
    icon = nativeImage.createFromPath(iconPath).resize({ width: 18, height: 18 });
  }

  tray = new Tray(icon);
  tray.setToolTip('Antigravity Toolkit 2.0 RU');

  tray.on('click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    } else {
      createWindow();
    }
  });

  updateTrayMenu();
}

function updateTrayMenu() {
  if (!tray) return;

  const slotsData = (cachedAllSlotsQuota && cachedAllSlotsQuota.slots) ? cachedAllSlotsQuota.slots : {};
  const activeSlot = (cachedAllSlotsQuota && cachedAllSlotsQuota.active_slot) ? cachedAllSlotsQuota.active_slot : 1;
  const activeData = slotsData[String(activeSlot)] || {};
  const activeEmail = activeData.email || 'Google Account';
  const activeG5h = (activeData.quota && activeData.quota.gemini_5h) ? activeData.quota.gemini_5h : null;
  const active5hPct = activeG5h ? `${activeG5h.remaining_pct}%` : 'активен';
  const activeReset = (activeG5h && activeG5h.formatted_reset) ? activeG5h.formatted_reset : '';

  const menuItems = [
    {
      label: 'Antigravity Toolkit 2.0 RU',
      enabled: false,
    },
    {
      label: `🟢 Слот #${activeSlot}: ${activeEmail} (${active5hPct})`,
      enabled: false,
    },
  ];

  if (activeReset) {
    menuItems.push({
      label: `⏳ Сброс 5ч: ${activeReset}`,
      enabled: false,
    });
  }

  menuItems.push({ type: 'separator' });
  menuItems.push({
    label: 'Смена Google-аккаунта (Keep-Alive):',
    enabled: false,
  });

  for (let i = 1; i <= 4; i++) {
    const sData = slotsData[String(i)];
    if (sData) {
      const isCur = (i === activeSlot);
      const sPct = (sData.quota && sData.quota.gemini_5h) ? ` [${sData.quota.gemini_5h.remaining_pct}%]` : '';
      menuItems.push({
        label: `${isCur ? '● ' : '○ '}Слот #${i}: ${sData.email || sData.name || 'Аккаунт'}${sPct}`,
        type: 'checkbox',
        checked: isCur,
        click: () => {
          switchSlotFromTray(i);
        },
      });
    } else {
      menuItems.push({
        label: `  Слот #${i}: (свободен)`,
        enabled: false,
      });
    }
  }

  menuItems.push({ type: 'separator' });
  menuItems.push({
    label: '🖥️ Открыть Antigravity Toolkit',
    click: () => {
      if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
      } else {
        createWindow();
      }
    },
  });
  menuItems.push({
    label: '🔄 Обновить квоты всех слотов',
    click: () => {
      syncAllSlotsBackground();
    },
  });
  menuItems.push({ type: 'separator' });
  menuItems.push({
    label: '🚪 Завершить Antigravity Toolkit',
    click: () => {
      isQuitting = true;
      app.quit();
    },
  });

  const contextMenu = Menu.buildFromTemplate(menuItems);
  tray.setContextMenu(contextMenu);
}

function switchSlotFromTray(slotNum) {
  execFile(PYTHON_BIN, [MAIN_PY, '--account-switch', String(slotNum)], { cwd: ROOT_DIR, env: DEFAULT_ENV }, () => {
    syncAllSlotsBackground();
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('account-switched-external', { slot: slotNum });
    }
  });
}

function syncAllSlotsBackground() {
  execFile(PYTHON_BIN, [MAIN_PY, '--refresh-all-slots'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 25000 }, () => {
    execFile(PYTHON_BIN, [MAIN_PY, '--all-slots-quota-json'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 25000 }, (err, stdout) => {
      if (!err && stdout) {
        try {
          cachedAllSlotsQuota = JSON.parse(stdout);
          updateTrayMenu();
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('all-slots-quota-updated', cachedAllSlotsQuota);
          }
        } catch (e) {}
      }
    });
  });
}

app.whenReady().then(() => {
  createWindow();
  createTray();
  syncAllSlotsBackground();

  // Фоновый Keep-Alive каждые 20 минут
  backgroundSyncTimer = setInterval(syncAllSlotsBackground, 20 * 60 * 1000);

  app.on('activate', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    } else {
      createWindow();
    }
  });
});

app.on('before-quit', () => {
  isQuitting = true;
  if (backgroundSyncTimer) {
    clearInterval(backgroundSyncTimer);
    backgroundSyncTimer = null;
  }
});

app.on('window-all-closed', () => {
  // На macOS приложение продолжает работу в системном трее (менюбаре)
});

// Window Controls
ipcMain.on('window-min', () => mainWindow && mainWindow.minimize());
ipcMain.on('window-max', () => {
  if (!mainWindow) return;
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
});
ipcMain.on('window-close', () => {
  if (mainWindow) {
    if (!isQuitting) {
      mainWindow.hide();
    } else {
      mainWindow.close();
    }
  }
});
ipcMain.on('open-external', (_event, url) => shell.openExternal(url));

// Stream Python Execution
function streamPythonCommand(args, event) {
  return new Promise((resolve) => {
    const sender = event ? event.sender : (mainWindow ? mainWindow.webContents : null);
    const proc = spawn(PYTHON_BIN, [MAIN_PY, ...args], {
      cwd: ROOT_DIR,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });

    const sendChunk = (data, isError = false) => {
      const clean = stripAnsi(data.toString());
      if (sender && !sender.isDestroyed()) {
        sender.send('log-chunk', { text: clean, isError, timestamp: new Date().toLocaleTimeString() });
      }
    };

    proc.stdout.on('data', (data) => sendChunk(data, false));
    proc.stderr.on('data', (data) => sendChunk(data, true));

    proc.on('close', (code) => {
      resolve({ success: code === 0, code });
    });

    proc.on('error', (err) => {
      sendChunk(`Ошибка запуска процесса: ${err.message}`, true);
      resolve({ success: false, error: err.message });
    });
  });
}

// IPC: Status
ipcMain.handle('get-status', async () => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--json-status'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 25000 }, (err, stdout) => {
      if (err) {
        resolve({ error: err.message, raw: stdout });
        return;
      }
      try {
        const data = JSON.parse(stdout);
        resolve(data);
      } catch (parseErr) {
        resolve({ error: `Ошибка парсинга JSON: ${parseErr.message}`, raw: stdout });
      }
    });
  });
});

// IPC: Quota
ipcMain.handle('get-quota', async () => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--quota-json'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 20000 }, (err, stdout) => {
      if (err) {
        resolve({ error: err.message, raw: stdout });
        return;
      }
      try {
        const data = JSON.parse(stdout);
        resolve(data);
      } catch (parseErr) {
        resolve({ error: `Ошибка парсинга JSON: ${parseErr.message}`, raw: stdout });
      }
    });
  });
});

// IPC: All slots quota (Keep-Alive status for all 4 slots)
ipcMain.handle('get-all-slots-quota', async () => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--all-slots-quota-json'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 25000 }, (err, stdout) => {
      if (err) {
        resolve({ error: err.message, raw: stdout });
        return;
      }
      try {
        const data = JSON.parse(stdout);
        cachedAllSlotsQuota = data;
        updateTrayMenu();
        resolve(data);
      } catch (parseErr) {
        resolve({ error: `Ошибка парсинга JSON: ${parseErr.message}`, raw: stdout });
      }
    });
  });
});

// IPC: Refresh all slots (Keep-Alive OAuth refresh)
ipcMain.handle('refresh-all-slots', async () => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--refresh-all-slots'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 30000 }, (err, stdout) => {
      syncAllSlotsBackground();
      resolve({ success: !err, message: stdout });
    });
  });
});

// IPC: Run actions
ipcMain.handle('run-action', async (event, action) => {
  const map = {
    all: ['--all'],
    localize: ['--localize'],
    unlock: ['--unlock'],
    restore: ['--restore'],
    diagnostics: ['--diagnostics'],
  };
  const args = map[action] || ['--all'];
  return streamPythonCommand(args, event);
});

// IPC: Switch language (ru / en)
ipcMain.handle('switch-language', async (event, lang) => {
  return streamPythonCommand(['--switch', lang], event);
});

// IPC: Account switch
ipcMain.handle('switch-account', async (event, slot) => {
  const res = await streamPythonCommand(['--account-switch', String(slot)], event);
  syncAllSlotsBackground();
  return res;
});

// IPC: Account save
ipcMain.handle('save-account', async (event, slot) => {
  const res = await streamPythonCommand(['--account-save', String(slot)], event);
  syncAllSlotsBackground();
  return res;
});

// IPC: Slot Wizard handlers
ipcMain.handle('wizard-start', async (_event, slot) => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--wizard-start', String(slot)], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 20000 }, (err, stdout) => {
      if (err) {
        resolve({ success: false, message: err.message });
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (parseErr) {
        resolve({ success: false, message: stdout });
      }
    });
  });
});

ipcMain.handle('wizard-status', async () => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--wizard-status'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 10000 }, (err, stdout) => {
      if (err) {
        resolve({ in_progress: false, error: err.message });
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (parseErr) {
        resolve({ in_progress: false, error: parseErr.message });
      }
    });
  });
});

ipcMain.handle('wizard-cancel', async () => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--wizard-cancel'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 20000 }, (err, stdout) => {
      syncAllSlotsBackground();
      if (err) {
        resolve({ success: false, message: err.message });
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (parseErr) {
        resolve({ success: true, message: stdout });
      }
    });
  });
});

// IPC: Auto-rotate toggle
ipcMain.handle('toggle-auto-rotate', async (event, enable) => {
  if (enable) {
    if (autoRotateProcess) {
      return { running: true, message: 'Авто-ротация уже активна.' };
    }
    autoRotateProcess = spawn(PYTHON_BIN, [MAIN_PY, '--auto-rotate'], {
      cwd: ROOT_DIR,
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });

    const sender = event.sender;
    autoRotateProcess.stdout.on('data', (data) => {
      if (sender && !sender.isDestroyed()) {
        sender.send('log-chunk', {
          text: `[AUTO-ROTATE] ${stripAnsi(data.toString())}`,
          isError: false,
          timestamp: new Date().toLocaleTimeString(),
        });
      }
    });

    autoRotateProcess.stderr.on('data', (data) => {
      if (sender && !sender.isDestroyed()) {
        sender.send('log-chunk', {
          text: `[AUTO-ROTATE ERR] ${stripAnsi(data.toString())}`,
          isError: true,
          timestamp: new Date().toLocaleTimeString(),
        });
      }
    });

    autoRotateProcess.on('close', () => {
      autoRotateProcess = null;
    });

    return { running: true, message: 'Служба авто-ротации токенов запущена.' };
  } else {
    if (autoRotateProcess) {
      autoRotateProcess.kill('SIGTERM');
      autoRotateProcess = null;
      return { running: false, message: 'Служба авто-ротации остановлена.' };
    }
    return { running: false, message: 'Служба авто-ротации не была запущена.' };
  }
});

ipcMain.handle('get-auto-rotate-status', () => {
  return { running: Boolean(autoRotateProcess) };
});

// IPC: Backup and Restore
ipcMain.handle('backup-create', async (event, type = 'chats') => {
  return streamPythonCommand(['--backup-create', type], event);
});

ipcMain.handle('backup-restore', async (event, file) => {
  return streamPythonCommand(['--backup-restore', file], event);
});

ipcMain.handle('backup-delete', async (_event, file) => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--backup-delete', file], { cwd: ROOT_DIR }, (err, stdout) => {
      resolve({ success: !err, message: stdout });
    });
  });
});

// IPC: Auto-Update (Safe zero-loss updates)
ipcMain.handle('check-update', async () => {
  return new Promise((resolve) => {
    execFile(PYTHON_BIN, [MAIN_PY, '--check-update'], { cwd: ROOT_DIR, env: DEFAULT_ENV, timeout: 25000 }, (err, stdout) => {
      if (err) {
        resolve({ success: false, error: err.message, raw: stdout });
        return;
      }
      try {
        const data = JSON.parse(stdout);
        resolve(data);
      } catch (parseErr) {
        resolve({ success: false, error: `Ошибка парсинга JSON: ${parseErr.message}`, raw: stdout });
      }
    });
  });
});

ipcMain.handle('apply-update', async (event) => {
  const res = await streamPythonCommand(['--apply-update'], event);
  if (res && res.success) {
    setTimeout(() => {
      isQuitting = true;
      app.quit();
    }, 2500);
  }
  return res;
});


