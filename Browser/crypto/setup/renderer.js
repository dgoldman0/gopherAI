let correctPhrase = [];

function callSetupWallet(password) 
{
    window.setupAPI.send('setup-wallet', password);
}

function populateRecoveryPhrase(recoveryPhrase) {
    const phraseContainer = document.querySelector('.recovery-phrase');
    correctPhrase = recoveryPhrase.split(/\s+/);
    correctPhrase.forEach(word => {
        const wordBubble = document.createElement('span');
        wordBubble.classList.add('phrase-bubble');
        wordBubble.innerText = word;
        phraseContainer.appendChild(wordBubble);
    });
}

window.setupAPI.on('wallet-setup-result', (result) => {
    populateRecoveryPhrase(result);
    document.getElementById('backup-card').classList.remove('hidden');
});

window.setupAPI.on('wallet-setup-error', (errorMessage) => {
    console.error('Wallet setup error:', errorMessage);
});

// These should callback to the wallet manager to do the next step
document.getElementById('next-to-backup').addEventListener('click', () => {
    const passwordInput = document.getElementById('password-input').value;
    const confirmPasswordInput = document.getElementById('confirm-password-input').value;
    const passwordError = document.getElementById('password-error');

    console.log("Checking password...");
    if(passwordInput && confirmPasswordInput && passwordInput === confirmPasswordInput) {
        passwordError.textContent = "";    
        document.getElementById('password-card').classList.add('hidden');
        // We need to call back to the wallet manager now and call   the next phase
        callSetupWallet(passwordInput);
    } else {
        passwordError.textContent = "Passwords do not match or are empty.";
    }
});

document.getElementById('next-to-naming').addEventListener('click', () => {
    document.getElementById('backup-card').classList.add('hidden');
    const textareaValue = document.getElementById('mnemonic-textarea').value.trim().split(/\s+/); // split by spaces

    if (JSON.stringify(textareaValue) !== JSON.stringify(correctPhrase)) {
        correctPhrase = [];
        document.getElementById('confirmation-card').classList.remove('hidden');
    } else {
        // Will have to show error.
    }
});

document.getElementById('next-to-welcome').addEventListener('click', () => {
    document.getElementById('naming-card').classList.add('hidden');
    document.getElementById('welcome-card').classList.remove('hidden');
});

document.getElementById('finish-setup').addEventListener('click', () => {
    // Whatever should happen when finishing the setup.
    window.close();  // This will just close the setup window.
});
