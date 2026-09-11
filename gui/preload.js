const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getStatus: () => ipcRenderer.invoke('get-status'),
  runAction: (action) => ipcRenderer.invoke('run-action', action),
  switchLanguage: (lang) => ipcRenderer.invoke('switch-language', lang),
  switchAccount: (slot) => ipcRenderer.invoke('switch-account', slot),
  saveAccount: (slot) => ipcRenderer.invoke('save-account', slot),
  toggleAutoRotate: (enable) => ipcRenderer.invoke('toggle-auto-rotate', enable),
  getAutoRotateStatus: () => ipcRenderer.invoke('get-auto-rotate-status'),
  onLog: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('log-chunk', handler);
    return () => ipcRenderer.removeListener('log-chunk', handler);
  },
  minimizeWindow: () => ipcRenderer.send('window-min'),
  maximizeWindow: () => ipcRenderer.send('window-max'),
  closeWindow: () => ipcRenderer.send('window-close'),
  openExternal: (url) => ipcRenderer.send('open-external', url),
});
