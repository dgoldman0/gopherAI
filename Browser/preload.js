const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('gopherAPI', {
    currentHost: () => ipcRenderer.sendSync('gopher-current-host'),
    currentPort: () => ipcRenderer.sendSync('gopher-current-port'),
    fetch: (selector, binary, save) => ipcRenderer.sendSync('gopher-fetch', selector, binary, save),
    scan: (selector) => ipcRenderer.sendSync('gopher-scan', selector),
    hop: (host, port) => ipcRenderer.sendSync('gopher-hop', host, port)
});

contextBridge.exposeInMainWorld('assistantAPI', {
    processInput: (input) => ipcRenderer.sendSync('assistant-process-input')
});