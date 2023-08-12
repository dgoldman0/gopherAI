const { app, BrowserWindow } = require('electron');
const { WalletManager } = require('./crypto/WalletManager.js');

let mainWindow;

let manager = new WalletManager();

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
