// These should callback to the wallet manager to do the next step
document.getElementById('next-to-import').addEventListener('click', () => {
    const passwordInput = document.getElementById('password-input').value;
    const confirmPasswordInput = document.getElementById('confirm-password-input').value;
    const passwordError = document.getElementById('password-error');

    if(passwordInput && confirmPasswordInput && passwordInput === confirmPasswordInput) {
        passwordError.textContent = "";
        // We need to call back to the wallet manager now and call 
    } else {
        passwordError.textContent = "Passwords do not match or are empty.";
    }
});
document.getElementById('next-to-naming').addEventListener('click', () => {
    document.getElementById('import-card').classList.add('hidden');
    document.getElementById('naming-card').classList.remove('hidden');
});

document.getElementById('next-to-welcome').addEventListener('click', () => {
    document.getElementById('naming-card').classList.add('hidden');
    document.getElementById('welcome-card').classList.remove('hidden');
});

document.getElementById('finish-setup').addEventListener('click', () => {
    // Whatever should happen when finishing the setup.
    window.close();  // This will just close the setup window.
});
