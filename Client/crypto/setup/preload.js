const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld(
    'setupAPI', {
        send: (channel, data) => {
            ipcRenderer.send(channel, data);
        },
        on: (channel, callback) => {
            ipcRenderer.on(channel, (event, ...args) => callback(...args));
        },
        once: (channel, callback) => {
            ipcRenderer.once(channel, (event, ...args) => callback(...args));
        },
        removeListener: (channel, callback) => {
            ipcRenderer.removeListener(channel, callback);
        }
    }
);
