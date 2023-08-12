const { Wallet, utils, HDNode } = require('ethers');
const Store = require('electron-store');
const { dialog, BrowserWindow } = require('electron')

const store = new Store();

// Really need to clean up code so it doesn't use both...

const crypto = require('crypto');

function generateKey(password, salt) {
    return crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha512');
}

// Should rename to just encrypt and decrypt. Plus it should be password, salt not password:salt
function encryptMnemonic(mnemonic, password) {
    const salt = crypto.randomBytes(16).toString('hex');
    const key = generateKey(password, salt);

    const cipher = crypto.createCipheriv('aes-256-cbc', key, Buffer.alloc(16, 0));
    let encrypted = cipher.update(mnemonic, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return salt + ':' + encrypted;
}

function decryptMnemonic(encryptedMnemonic, password) {
    const [salt, encryptedData] = encryptedMnemonic.split(':');
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
        this.initialize();
        this.mainWindow = mainWindow;
    }

    // Unlock the wallet using the password
    async unlock() {
        // Popup password request
        // Check against hash
    }

    // Bring up the setup window
    async popupSetupWindow() {
        // Create the browser window.
        let setupWindow = new BrowserWindow({
            width: 400,
            height: 300,
            webPreferences: {
                nodeIntegration: false, // caution: this can introduce security risks
                contextIsolation: true
            }
        });

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

    async initialize() {
        if (!store.get('walletRoot')) {
            console.log("Initializing...")
            
            this.popupSetupWindow();
        }
    }

    async createWallet() {
        this.password = password;
        salt = this.generateSalt();
        store.set('password_salt', salt);
        store.set('wallet_password', this.hashPassword(password, salt));
        this.createWalletRoot();
    }

    async createWalletRoot() {
        const wallet = Wallet.createRandom();
        const _mnemonic = wallet.mnemonic.phrase;

        const salt = this.generateSalt();
        
        // Encrypt and store mnemonic.
        const encryptedMnemonic = encryptMnemonic(_mnemonic, this.password, salt);
        
        const walletRoot = {};
        walletRoot.mnemonic = encryptedMnemonic;
        walletRoot.salt = salt;
        walletRoot.addresses.push(wallet.address);
        walletRoot.address_uses = 1;
        // Save back to the store
        store.set('walletRoot', walletRoot);

        return wallet.address;  // Return derived address
    }

    // Generate new HD Wallet address from root mnemonic
    async addNewAddress() {
        const walletRootData = store.get('walletRoot');
        if (!walletRootData) throw new Error("Wallet root not found.");

        // Decrypt mnemonic
        const mnemonic = decryptMnemonic(walletRootData.mnemonic, this.password, walletRootData.salt);

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
