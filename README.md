# ChatDev

[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML) [![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS) [![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org) [![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript) [![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com) [![Socket.io](https://img.shields.io/badge/Socket.io-010101?style=flat&logo=socket.io&logoColor=white)](https://socket.io) [![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white)](https://www.mongodb.com) ![GitHub repo size](https://img.shields.io/github/repo-size/Jalpan04/chatdev) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A real-time instant chat service built using Flask, Flask-SocketIO, and MongoDB, featuring direct messaging, voice notes, chunked file uploads, and an integrated inline Python code compiler.

## Features

- **Real-Time Direct Messaging**: Instant messaging powered by WebSockets (Socket.IO) for dynamic, low-latency communication.
- **Voice Messages**: Record and send voice notes directly in the chat panel (saved as base64-encoded webm files).
- **Chunked File Uploads**: High-performance upload pipeline supporting chunks to transfer large files (up to 10 GB limit configured) with real-time progress indicators.
- **Inline Python Compiler**: Write, execute, and preview output from Python scripts within the chat interface using a secure execution process with time limits.
- **Friend Request System**: Secure friend lookup, request queue, accept, and reject options to build your messaging contact list.
- **Message & Upload History**: Persistent storage of past texts, audio files, and attachments using MongoDB.

## Tech Stack

- **Backend Framework**: Flask (Python)
- **Real-Time Server**: Flask-SocketIO (WebSockets)
- **Database**: MongoDB (via Flask-PyMongo)
- **Encryption**: Bcrypt (password hashing)
- **Frontend**: HTML5, CSS3, JavaScript (WebSocket client integration)

## Directory Structure

```
├── app.py                # Main Flask application, Socket.IO handlers, and routes
├── compiler.py           # Secure subprocess runner for compiling Python scripts
├── chatdev.png           # Interface illustration
├── favicon.ico           # Web icon
├── static/               # Style sheets, client-side scripts, and UI images
├── templates/            # HTML views (login, signup, chat panel, compiler)
├── .gitignore            # Git exclusion rules
└── LICENSE               # MIT License
```

## Getting Started

### Prerequisites

- Python 3.8 or higher.
- MongoDB instance running locally (`mongodb://localhost:27017`) or configured MongoDB Atlas URI.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Jalpan04/chatdev.git
   ```
2. Navigate to the project directory:
   ```bash
   cd chatdev
   ```
3. Install the required dependencies:
   ```bash
   pip install Flask Flask-SocketIO Flask-PyMongo bcrypt werkzeug
   ```

### Configuration & Running

1. Ensure MongoDB is active on your system.
2. Run the application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to `http://localhost:5000` to register a user, log in, add friends, and start chatting.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
