const { Wallet, utils, HDNode } = require('ethers');
const Store = require('electron-store');
const { dialog, BrowserWindow } = require('electron')
const path = require('path');

const store = new Store();
console.log(store);
const crypto = require('crypto');

function generateKey(password, salt) {
    return crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha512');
}

// Should rename to just encrypt and decrypt. Plus it should be password, salt not password:salt
function encrypt(mnemonic, password, salt) {
    const key = generateKey(password, salt);

    const cipher = crypto.createCipheriv('aes-256-cbc', key, Buffer.alloc(16, 0));
    let encrypted = cipher.update(mnemonic, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return encrypted;
}

function decrypt(encryptedMnemonic, password, salt) {
    const key = generateKey(password, salt);

    const decipher = crypto.createDecipheriv('aes-256-cbc', key, Buffer.alloc(16, 0));
    let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
}

class WalletManager {
    constructor() {
        this.password = null;
    }

    initialize(mainWindow) {
        console.log("Initializing...")
        this.mainWindow = mainWindow;
        if (!store.get('walletRoot')) {
            console.log("Setting up wallet...");            
            this.popupSetupWindow();
        }
    }

    // Unlock the wallet using the password
    async unlock() {
        // Popup password request
        // Check against hash
    }

    // Bring up the setup window
    async popupSetupWindow() {
        let setupWindow = new BrowserWindow({
            width: 550,
            height: 400,
            webPreferences: {
                nodeIntegration: false, // caution: this can introduce security risks
                contextIsolation: true,
                scrollBounce: true,
                preload: path.join(__dirname, 'setup/preload.js')
            }
        });

        setupWindow.setMenu(null);
        // Load the index page for the setup interface
        await setupWindow.loadFile('./crypto/setup/index.html');

        // Open the DevTools (optional).
        // setupWindow.webContents.openDevTools();

        // Emitted when the window is closed.
        setupWindow.on('closed', function () {
            // Dereference the window object. 
            // Usually, you'd store windows in an array if your app supports multi windows.
            // This is the time when you should delete the corresponding element.
            setupWindow = null;
        });
    }
    
    // Generates a unique salt for encryption
    generateSalt() {
        return crypto.randomBytes(16).toString('hex');
    }
   
    hashPassword(password, salt) {
        const hash = crypto.pbkdf2Sync(password, salt, 10000, 512, 'sha512');
        return hash.toString('hex'); // Returns the hashed password
    }

    async setupWallet(password) {
        this.password = password;
        let salt = this.generateSalt();
        store.set('password_salt', salt);
        store.set('hashed_password', this.hashPassword(password, salt));
        return this.createWalletRoot();
    }

    async importWallet() {

    }

    // Creates a new wallet root. 
    async createWalletRoot() {
        const wallet = Wallet.createRandom();
        const _mnemonic = wallet.mnemonic.phrase;

        const salt = this.generateSalt();
        
        // Encrypt and store mnemonic.
        const encryptedMnemonic = encrypt(_mnemonic, this.password, salt);
        
        const walletRoot = {};
        walletRoot.mnemonic = encryptedMnemonic;
        walletRoot.salt = salt;
        walletRoot.address_uses = 1;
        // Save back to the store
        store.set('walletRoot', walletRoot);

        return _mnemonic;  // Return derived address
    }

    // Generate new HD Wallet address from root mnemonic
    async addNewAddress() {
        const walletRootData = store.get('walletRoot');
        if (!walletRootData) throw new Error("Wallet root not found.");

        // Decrypt mnemonic
        const mnemonic = decrypt(walletRootData.mnemonic, this.password, walletRootData.salt);

        // Get the next address
        const nextAddress = this.getNthAddress(mnemonic, walletRootData.address_uses);

        walletRootData.addresses.push(nextAddress);
        walletRootData.address_uses += 1;
        // Save back to the store
        store.set('walletRoot', walletRootData);

        return nextAddress;  // Return derived address
    }

    // Derive and return the nth address from a root mnemonic (HD wallet functionality)
    async getNthAddress(mnemonic, index) {
        const root = HDNode.fromMnemonic(mnemonic);
        const walletNode = root.derivePath("m/44'/60'/0'/0/" + index);
        const wallet = new Wallet(walletNode.privateKey);
        return wallet.address;
    }

    // Add other functions as needed like sendTransaction, getBalance, etc.
}

module.exports = { WalletManager };
