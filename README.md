# ChatDev

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
