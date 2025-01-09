const username = "{{ username }}"; // Get the username from the template context
const socket = io.connect(`${location.protocol}//${document.domain}:${location.port}`, {
    query: { username: username }
});

let selectedUser = null;
let messageHistory = {}; // Stores message history for each user

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

// Update the UI with a new user list
socket.on('user_list', (users) => {
    console.log('Online users:', users); // Debug log
    const userList = document.getElementById('user-list');
    userList.innerHTML = ''; // Clear existing list
    users.forEach((user) => {
        if (user !== username) {
            const li = document.createElement('li');
            li.textContent = user;
            li.onclick = () => openChat(user); // Attach click handler
            userList.appendChild(li);
        }
    });
});


// Open chat with selected user and display message history
function openChat(user) {
    selectedUser = user;
    const messages = document.getElementById('messages');
    messages.innerHTML = ''; // Clear current chat
    const title = document.querySelector('h3');
    title.textContent = `Chat with ${user}`;

    displayMessageHistory(user);
    unreadMessages[user] = 0;
    updateBadge(user);
    document.getElementById('input-container').style.display = 'flex';

    highlightSelectedUser(user);
}

// Display message history for a user
function displayMessageHistory(user) {
    const messages = document.getElementById('messages');
    if (messageHistory[user]) {
        messageHistory[user].forEach(message => {
            const div = document.createElement('div');
            div.textContent = message.text || '';
            div.classList.add(message.sender === username ? 'message-sender' : 'message-receiver');
            if (message.audio) {
                const audio = document.createElement('audio');
                audio.src = message.audio;
                audio.controls = true;
                div.appendChild(audio);
            }
            messages.appendChild(div);
        });
    }
}

// Highlight the selected user in the user list
function highlightSelectedUser(user) {
    const userListItems = document.querySelectorAll('#user-list li');
    userListItems.forEach(item => item.classList.remove('active'));
    const selectedItem = [...userListItems].find(item => item.textContent === user);
    selectedItem?.classList.add('active');
}

// Listen for incoming messages and display them
function handleIncomingMessage(data, type = 'text') {
    if (data.sender === selectedUser || data.recipient === selectedUser) {
        const messageDiv = document.getElementById('messages');
        const message = document.createElement('div');
        message.classList.add('message', data.sender === username ? 'you' : 'other');

        if (type === 'text') {
            message.textContent = `${data.sender}: ${data.message}`;
        } else if (type === 'audio') {
            const audioElement = document.createElement('audio');
            audioElement.controls = true;
            audioElement.src = data.audio_url;
            message.appendChild(audioElement);
        }

        messageDiv.appendChild(message);
        messageDiv.scrollTop = messageDiv.scrollHeight;

        saveMessageHistory(data);
    }
}

// Save the message to history
function saveMessageHistory(data) {
    if (!messageHistory[selectedUser]) {
        messageHistory[selectedUser] = [];
    }
    messageHistory[selectedUser].push(data);
}

// Listen for incoming text messages
socket.on('receive_message', function(data) {
    handleIncomingMessage(data, 'text');
});

// Listen for incoming voice messages
socket.on('receive_voice_message', function(data) {
    handleIncomingMessage(data, 'audio');
});

// Send a text message
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value;

    if (!selectedUser || !message.trim()) {
        alert('Please select a user and enter a message.');
        return;
    }

    socket.emit('send_message', {
        sender: username,
        recipient: selectedUser,
        message: message
    });

    const messageDiv = document.getElementById('messages');
    const userMessage = document.createElement('div');
    userMessage.classList.add('message', 'you');
    userMessage.textContent = `You: ${message}`;
    messageDiv.appendChild(userMessage);

    messageInput.value = '';
    messageDiv.scrollTop = messageDiv.scrollHeight;

    saveMessageHistory({
        sender: username,
        recipient: selectedUser,
        message: message
    });
}

// Setup voice message functionality
const voiceButton = document.getElementById('voice-button');
let mediaRecorder;
let audioChunks = [];

voiceButton.addEventListener('mousedown', async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
        alert('Audio recording is not supported in this browser.');
        return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = [];
        const reader = new FileReader();
        reader.onload = () => {
            const base64Audio = reader.result.split(',')[1];
            if (!selectedUser) {
                alert('Please select a user to send a voice message.');
                return;
            }

            socket.emit('send_voice_message', {
                sender: username,
                recipient: selectedUser,
                audio_blob: base64Audio
            });
        };
        reader.readAsDataURL(audioBlob);
    };

    mediaRecorder.start();
});

voiceButton.addEventListener('mouseup', () => {
    if (mediaRecorder?.state !== 'inactive') {
        mediaRecorder.stop();
    }
});

// Allow sending text messages on Enter key press
document.getElementById('message-input').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        sendMessage();
    }
});
