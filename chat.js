const username = "{{ username }}";
const socket = io.connect(`${location.protocol}//${document.domain}:${location.port}`, {
    query: { username: username }
});

let selectedUser = null;

// Listen for the user list
socket.on('user_list', function(users) {
    const userList = document.getElementById('user-list');

    // Clear previous user list
    userList.innerHTML = '';

    users.forEach(function(user) {
        if (user !== username) {
            const li = document.createElement('li');
            li.textContent = user;
            li.onclick = function() {
                openChat(user);
            };
            userList.appendChild(li);
        }
    });
});

// Open chat with the selected user
function openChat(user) {
    selectedUser = user;
    const messageDiv = document.getElementById('messages');
    messageDiv.innerHTML = ''; // Clear current messages
    const title = document.querySelector('h3');
    if (title) {
        title.textContent = `Chat with ${user}`;
    }

    // Highlight the selected user
    const userListItems = document.querySelectorAll('#user-list li');
    userListItems.forEach(item => item.classList.remove('active'));
    const selectedItem = [...userListItems].find(item => item.textContent === user);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
}

// Listen for incoming messages
socket.on('receive_message', function(data) {
    if (data.sender === selectedUser || data.recipient === selectedUser) {
        const messageDiv = document.getElementById('messages');
        const message = document.createElement('div');
        message.classList.add('message', data.sender === username ? 'you' : 'other');
        message.textContent = `${data.sender}: ${data.message}`;
        messageDiv.appendChild(message);
        messageDiv.scrollTop = messageDiv.scrollHeight; // Scroll to the latest message
    }
});

// Send message to the selected user
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value;

    if (!selectedUser) {
        alert('Please select a user to send a message.');
        return;
    }

    if (message.trim()) {
        socket.emit('send_message', {
            sender: username,
            recipient: selectedUser,
            message: message
        });

        // Display the user's message immediately
        const messageDiv = document.getElementById('messages');
        const userMessage = document.createElement('div');
        userMessage.classList.add('message', 'you');
        userMessage.textContent = `You: ${message}`;
        messageDiv.appendChild(userMessage);

        messageInput.value = ''; // Clear input after sending
        messageDiv.scrollTop = messageDiv.scrollHeight; // Scroll to the latest message
    }
}

const messageInput = document.getElementById('message-input');
messageInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent default Enter behavior (new line or form submission)
        sendMessage();  // Call sendMessage function to send the message
    }
});
