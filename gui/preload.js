const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  getStatus: () => ipcRenderer.invoke('get-status'),
  runAction: (action) => ipcRenderer.invoke('run-action', action),
  switchLanguage: (lang) => ipcRenderer.invoke('switch-language', lang),
  switchAccount: (slot) => ipcRenderer.invoke('switch-account', slot),
  saveAccount: (slot) => ipcRenderer.invoke('save-account', slot),
  wizardStart: (slot) => ipcRenderer.invoke('wizard-start', slot),
  wizardStatus: () => ipcRenderer.invoke('wizard-status'),
  wizardCancel: () => ipcRenderer.invoke('wizard-cancel'),
  toggleAutoRotate: (enable) => ipcRenderer.invoke('toggle-auto-rotate', enable),
  getAutoRotateStatus: () => ipcRenderer.invoke('get-auto-rotate-status'),
  getQuota: () => ipcRenderer.invoke('get-quota'),
  getAllSlotsQuota: () => ipcRenderer.invoke('get-all-slots-quota'),
  refreshAllSlots: () => ipcRenderer.invoke('refresh-all-slots'),
  onSlotsUpdated: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('all-slots-quota-updated', handler);
    return () => ipcRenderer.removeListener('all-slots-quota-updated', handler);
  },
  onAccountSwitched: (callback) => {
    const handler = (_event, data) => callback(data);
    ipcRenderer.on('account-switched-external', handler);
    return () => ipcRenderer.removeListener('account-switched-external', handler);
  },
  createBackup: (type) => ipcRenderer.invoke('backup-create', type),
  restoreBackup: (file) => ipcRenderer.invoke('backup-restore', file),
  deleteBackup: (file) => ipcRenderer.invoke('backup-delete', file),
  checkUpdate: () => ipcRenderer.invoke('check-update'),
  applyUpdate: () => ipcRenderer.invoke('apply-update'),
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
