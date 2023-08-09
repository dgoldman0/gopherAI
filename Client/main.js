const { app, BrowserWindow } = require('electron');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      scrollBounce: true
    }
  });

  mainWindow.webContents.openDevTools();
  mainWindow.loadFile('index.html');
  mainWindow.on('closed', function() {
    mainWindow = null;
  });
}

app.commandLine.appendSwitch('disable-gpu');
app.on('ready', createWindow);
app.on('window-all-closed', function() {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
