import { users } from './database.js';
import { translations, guideSteps } from './translations.js';

// --- DOM Elements ---
const splashScreen = document.getElementById('splash-screen');
const languageSelectionScreen = document.getElementById('language-selection-screen');
const languageSelector = document.getElementById('language-selector');
const languageSubmitBtn = document.getElementById('language-submit-btn');
const loginModal = document.getElementById('login-modal');
const mainChatContainer = document.getElementById('main-chat-container');
const modalTitle = document.getElementById('modal-title');
const modalMessage = document.getElementById('modal-message');
const signupFields = document.getElementById('signup-fields');
const firstNameInput = document.getElementById('first-name-input');
const lastNameInput = document.getElementById('last-name-input');
const fisherIdInput = document.getElementById('fisher-id-input');
const phoneInput = document.getElementById('phone-input');
const authActionBtn = document.getElementById('auth-action-btn');
const switchToSignupLink = document.querySelector('.form-switcher');
const profileContainer = document.getElementById('profile-container');
const profileIcon = document.getElementById('profile-icon');
const logoutDropdown = document.getElementById('logout-dropdown');
const welcomeMessage = document.getElementById('welcome-message');
const logoutBtn = document.getElementById('logout-btn');
const visualGuideBtn = document.getElementById('visual-guide-btn');
const guideModal = document.getElementById('guide-modal');
const closeGuideBtn = document.getElementById('close-guide-btn');
const guideTitle = document.getElementById('guide-title');
const guideStepsContainer = document.getElementById('guide-steps');

let isLoginMode = true;
let currentLanguage = 'en';

// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', () => {
    // Start with splash screen
    setTimeout(() => {
        splashScreen.classList.add('hidden');
        languageSelectionScreen.classList.remove('hidden');
    }, 3000);

    loadTheme();
});

// --- Language Selection ---
languageSubmitBtn.addEventListener('click', () => {
    currentLanguage = languageSelector.value;
    languageSelectionScreen.classList.add('hidden');
    updateUIText();
    checkLoginStatus();
});

// --- Authentication Flow ---
function checkLoginStatus() {
    const loggedInUser = JSON.parse(sessionStorage.getItem('loggedInUser'));
    if (loggedInUser) {
        showChatView(loggedInUser);
    } else {
        showLoginView();
    }
}

function showChatView(user) {
    mainChatContainer.classList.remove('hidden');
    loginModal.classList.add('hidden');
    profileContainer.classList.remove('hidden');
    welcomeMessage.textContent = `${translations[currentLanguage].welcome}, ${user.firstName}!`;
}

function showLoginView() {
    mainChatContainer.classList.add('hidden');
    loginModal.classList.remove('hidden');
    profileContainer.classList.add('hidden');
}

// --- Event Listeners ---
profileIcon.addEventListener('click', () => {
    logoutDropdown.classList.toggle('hidden');
});

logoutBtn.addEventListener('click', () => {
    sessionStorage.removeItem('loggedInUser');
    logoutDropdown.classList.add('hidden');
    checkLoginStatus();
});

loginModal.addEventListener('click', (e) => {
    if (e.target === loginModal) loginModal.classList.add('hidden');
});

switchToSignupLink.addEventListener('click', (e) => {
    if (e.target.tagName === 'A') {
        e.preventDefault();
        isLoginMode = !isLoginMode;
        updateAuthForm();
    }
});

authActionBtn.addEventListener('click', handleAuthAction);
visualGuideBtn.addEventListener('click', showVisualGuide);
closeGuideBtn.addEventListener('click', () => guideModal.classList.add('hidden'));

// --- Functions ---
function updateAuthForm() {
    signupFields.classList.toggle('hidden', isLoginMode);
    updateUIText();
}

function handleAuthAction() {
    const fisherId = fisherIdInput.value.trim();
    const phone = phoneInput.value.trim();
    const firstName = firstNameInput.value.trim();
    const lastName = lastNameInput.value.trim();

    if (!fisherId || !phone || (!isLoginMode && (!firstName || !lastName))) {
        showModalMessage(translations[currentLanguage].fillAllFields);
        return;
    }

    const userExists = users.find(u => u.fisherId === fisherId);

    if (isLoginMode) {
        if (userExists && userExists.phone === phone) {
            loginSuccess(userExists);
        } else {
            showModalMessage(translations[currentLanguage].invalidCredentials);
        }
    } else { // Signup
        if (userExists) {
            showModalMessage(translations[currentLanguage].accountExists);
            setTimeout(() => loginSuccess(userExists), 1500);
        } else {
            const newUser = { fisherId, phone, firstName, lastName };
            users.push(newUser); // Simulate adding to DB
            showModalMessage(translations[currentLanguage].signupSuccess);
            setTimeout(() => loginSuccess(newUser), 1500);
        }
    }
}

function loginSuccess(user) {
    sessionStorage.setItem('loggedInUser', JSON.stringify(user));
    loginModal.classList.add('hidden');
    checkLoginStatus();
    fisherIdInput.value = '';
    phoneInput.value = '';
    firstNameInput.value = '';
    lastNameInput.value = '';
    modalMessage.classList.add('hidden');
}

function showModalMessage(message) {
    modalMessage.textContent = message;
    modalMessage.classList.remove('hidden');
}

function showVisualGuide() {
    guideTitle.textContent = translations[currentLanguage].guideTitle;
    const steps = guideSteps[currentLanguage];
    guideStepsContainer.innerHTML = steps.map((step, index) => `<p><b>${index + 1}.</b> ${step}</p>`).join('');
    guideModal.classList.remove('hidden');
}

function updateUIText() {
    const t = translations[currentLanguage];
    modalTitle.textContent = isLoginMode ? t.login : t.signup;
    authActionBtn.textContent = isLoginMode ? t.login : t.signup;
    switchToSignupLink.innerHTML = isLoginMode ? t.signupPrompt : t.loginPrompt;
    document.getElementById('user-input').placeholder = t.typeMessage;
    firstNameInput.placeholder = t.firstName;
    lastNameInput.placeholder = t.lastName;
    fisherIdInput.placeholder = t.fisherId;
    phoneInput.placeholder = t.phone;
}


// --- Chat Functionality (Placeholder) ---
const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

sendBtn.addEventListener('click', () => {
    const message = userInput.value.trim();
    if (message) {
        appendMessage('user', message);
        userInput.value = '';
    }
});

function appendMessage(sender, text) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    messageElement.textContent = text;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// --- Theme switcher ---
const themeSwitcher = document.getElementById('theme-switcher');
themeSwitcher.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
});

function loadTheme() {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
    }
}
