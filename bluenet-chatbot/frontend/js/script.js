const chatBox = document.querySelector('.chat-box');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        sendMessage();
    }
});

async function sendMessage() {
    const userMessage = userInput.value;
    if (userMessage.trim() !== '') {
        appendMessage('user', userMessage);
        userInput.value = '';

        showTypingIndicator();

        const response = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: userMessage })
        });

        hideTypingIndicator();

        if (response.ok) {
            const data = await response.json();
            appendMessage('bot', data.response);
        } else {
            appendMessage('bot', 'Sorry, something went wrong.');
        }
    }
}

function appendMessage(sender, message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', `${sender}-message`);
    messageElement.innerText = message;
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
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
