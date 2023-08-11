const { contextBridge, ipcRenderer } = require('electron');

const GopherClient = require('./GopherClient.js');

console.log("Starting Gopher client...");
const gc = new GopherClient('localhost', 10070);

contextBridge.exposeInMainWorld('gopherAPI', {
    currentHost: () => gopher.host,
    currentPort: () => gopher.port,
    fetch: (selector, binary, save) => {
        return gopher.fetch(selector, binary, save);
    },
    scan: (selector) => {
        return gopher.scan(selector);
    },
    hop: (host, port) => {
        gopher.setHost(host, port);
    }
});