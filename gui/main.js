const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn, execFile } = require('child_process');

let mainWindow = null;
let autoRotateProcess = null;

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

const { rootDir: ROOT_DIR, mainPy: MAIN_PY } = resolvePythonPaths();
const PYTHON_BIN = process.env.PYTHON || 'python3';

console.log('[Antigravity GUI] ROOT_DIR:', ROOT_DIR);
console.log('[Antigravity GUI] MAIN_PY:', MAIN_PY);

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

  mainWindow.on('closed', () => {
    mainWindow = null;
    if (autoRotateProcess) {
      autoRotateProcess.kill();
      autoRotateProcess = null;
    }
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Window Controls
ipcMain.on('window-min', () => mainWindow && mainWindow.minimize());
ipcMain.on('window-max', () => {
  if (!mainWindow) return;
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize();
});
ipcMain.on('window-close', () => mainWindow && mainWindow.close());
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
    execFile(PYTHON_BIN, [MAIN_PY, '--json-status'], { cwd: ROOT_DIR, timeout: 20000 }, (err, stdout) => {
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
    execFile(PYTHON_BIN, [MAIN_PY, '--quota-json'], { cwd: ROOT_DIR, timeout: 15000 }, (err, stdout) => {
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
  return streamPythonCommand(['--account-switch', String(slot)], event);
});

// IPC: Account save
ipcMain.handle('save-account', async (event, slot) => {
  return streamPythonCommand(['--account-save', String(slot)], event);
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

