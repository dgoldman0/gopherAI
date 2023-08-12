const { ipcMain, app, BrowserWindow } = require('electron');
const { WalletManager } = require('./crypto/WalletManager.js');

let mainWindow;

let manager = new WalletManager();

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

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      scrollBounce: true
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
