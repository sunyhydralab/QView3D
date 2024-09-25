// preload.js
import { contextBridge, ipcRenderer } from 'electron';
const settings = require('electron-settings');

// Expose a safe API to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    openDevTools: () => ipcRenderer.send('open-dev-tools'),
});

contextBridge.exposeInMainWorld('configStore', {
    get: (key) => ipcRenderer.invoke('config-store-get', key),
    set: (key, value) => ipcRenderer.invoke('config-store-set', key, value),
});