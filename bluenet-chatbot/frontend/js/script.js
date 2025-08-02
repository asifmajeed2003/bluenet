const chatBox = document.querySelector('.chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const themeSwitcher = document.getElementById('theme-switcher');

let mediaRecorder;
let audioChunks = [];

// Theme switcher
themeSwitcher.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    if (document.body.classList.contains('dark-mode')) {
        themeSwitcher.firstElementChild.src = "https://img.icons8.com/ios-filled/50/FFFFFF/moon-symbol.png";
        localStorage.setItem('theme', 'dark-mode');
    } else {
        themeSwitcher.firstElementChild.src = "https://img.icons8.com/ios-filled/50/000000/sun.png";
        localStorage.setItem('theme', 'light-mode');
    }
});

function loadTheme() {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark-mode') {
        document.body.classList.add('dark-mode');
        themeSwitcher.firstElementChild.src = "https://img.icons8.com/ios-filled/50/FFFFFF/moon-symbol.png";
    }
}

loadTheme();

sendBtn.addEventListener('click', () => sendMessage());
userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

micBtn.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        micBtn.firstElementChild.src = "https://img.icons8.com/ios-filled/50/000000/microphone.png";
    } else {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                micBtn.firstElementChild.src = "https://img.icons8.com/ios-filled/50/FA5252/stop-circled.png";

                mediaRecorder.addEventListener("dataavailable", event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener("stop", () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    sendAudio(audioBlob);
                    audioChunks = [];
                });
            })
            .catch(error => {
                console.error("Error accessing microphone:", error);
                appendMessage('bot', 'Could not access microphone. Please allow microphone access in your browser settings.');
            });
    }
});

async function sendMessage(message) {
    const userMessage = message || userInput.value;
    if (userMessage.trim() !== '') {
        appendMessage('user', userMessage);
        userInput.value = '';

        showTypingIndicator();

        const response = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage, history: getChatHistory() })
        });

        hideTypingIndicator();

        if (response.ok) {
            const data = await response.json();
            appendMessage('bot', data.response);
            playAudio(data.response);
        } else {
            appendMessage('bot', 'Sorry, something went wrong.');
        }
    }
}

async function sendAudio(audioBlob) {
    showTypingIndicator();
    const formData = new FormData();
    formData.append('file', audioBlob);

    const response = await fetch('http://localhost:5000/speech-to-text', {
        method: 'POST',
        body: formData
    });

    hideTypingIndicator();

    if (response.ok) {
        const data = await response.json();
        if (data.transcript) {
            sendMessage(data.transcript);
        } else {
            appendMessage('bot', 'Sorry, I could not understand what you said.');
        }
    } else {
        appendMessage('bot', 'Sorry, something went wrong with speech recognition.');
    }
}

function appendMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    messageElement.innerText = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Store message in history
    const history = getChatHistory();
    history.push({role: sender, content: message});
    sessionStorage.setItem('chatHistory', JSON.stringify(history));
}

function getChatHistory() {
    const history = sessionStorage.getItem('chatHistory');
    return history ? JSON.parse(history) : [];
}

async function playAudio(text) {
    const response = await fetch('http://localhost:5000/text-to-speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text: text })
    });

    if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    }
}

function showTypingIndicator() {
    const typingIndicator = document.createElement('div');
    typingIndicator.classList.add('message', 'bot-message', 'typing-indicator');
    typingIndicator.innerHTML = '<span></span><span></span><span></span>';
    chatBox.appendChild(typingIndicator);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}
