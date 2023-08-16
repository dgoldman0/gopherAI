const { ipcMain, app, BrowserWindow } = require('electron');
const { WalletManager } = require('./crypto/WalletManager.js');
const path = require('path');

const { Assistant } = require(path.join(__dirname, 'Assistant.js'));
const { GopherClient } = require(path.join(__dirname, 'Gopher.js'));

let mainWindow;

let manager = new WalletManager();

const assistant = new Assistant(process.env.OPENAI_KEY);

ipcMain.on('assistant-process-input', (event, input) => {
  assistant.processInput(input).then(result => {
    event.reply('assistant-response', result); 
  }).catch(error => {
    console.log(error);
    event.reply('assistant-error', error.message);
  });
});

// Set up IPC listeners
ipcMain.on('setup-wallet', (event, password) => {
  manager.setupWallet(password).then(result => {
      event.reply('wallet-setup-result', result);
  }).catch(error => {
      console.log(error);
      // Handle the error or send it back to the renderer
      event.reply('wallet-setup-error', error.message);
  });
});

const gc = new GopherClient('localhost', 10070);

ipcMain.on('gopher-current-host', (event) => {
  event.returnValue = gc.host;
});

ipcMain.on('gopher-current-port', (event) => {
  event.returnValue = gc.port;
});

ipcMain.on('gopher-fetch', (event, selector, binary, save) => {
    gc.fetch(selector, binary, save)
       .then(result => {
           event.reply('gopher-fetch-response', result);
       })
       .catch(error => {
          console.log(error);
          event.reply('gopher-fetch-error', error.message);
       });
});

ipcMain.on('gopher-scan', (event, selector) => {
    gc.scan(selector)
       .then(result => {
          event.reply('gopher-scan-response', result);
       })
       .catch(error => {
          console.log(error);
          event.reply('gopher-scan-error', error.message);
       });
});

ipcMain.on('gopher-hop', (event, host, port) => {
    gc.setHost(host, port); 
    event.returnValue = { success: true };
});

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      scrollBounce: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });
  
  mainWindow.webContents.openDevTools();
  mainWindow.loadFile('index.html');
  mainWindow.on('closed', function() {
    mainWindow = null;
  });
  manager.initialize(manager);
}

app.commandLine.appendSwitch('disable-gpu');
app.on('ready', createWindow);
app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
