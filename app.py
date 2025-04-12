import base64
import logging
import os
import time
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, emit
from flask_pymongo import PyMongo
import re
from compiler import run_code
from werkzeug.utils import secure_filename
from bson import ObjectId


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB file limit

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/chatapp"  # Use MongoDB Atlas if needed
mongo = PyMongo(app)

socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10 * 1024 * 1024 * 1024)  # 10GB

online_users = {}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create MongoDB indexes for performance
def create_indexes():
    try:
        mongo.db.users.create_index("username", unique=True)
        mongo.db.messages.create_index([("sender", 1), ("recipient", 1), ("timestamp", 1)])
        mongo.db.voice_messages.create_index([("sender", 1), ("recipient", 1), ("timestamp", 1)])
        mongo.db.files.create_index([("sender", 1), ("recipient", 1), ("timestamp", 1)])
        logger.info("MongoDB indexes created successfully.")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

create_indexes()

# Helper function to validate user friendship
def are_friends(sender, recipient):
    sender_user = mongo.db.users.find_one({"username": sender})
    return sender_user and recipient in sender_user.get("friends", [])


# Home route
@app.route('/')
def index():
    return render_template('welcome.html')


# Route for signup page
@app.route('/signup')
def signup_page():
    return render_template('signup.html')


# Signup handling route (POST)
@app.route('/signup', methods=['POST'])
def signup():
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([username, email, password, confirm_password]):
            return jsonify({"error": "All fields are required"}), 400

        if password != confirm_password:
            return jsonify({"error": "Passwords do not match"}), 400

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        existing_user = mongo.db.users.find_one({"username": username})
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password,
            "friends": [],
            "friend_requests": []
        })

        logger.info(f"User signed up: {username}")
        return redirect(url_for('chat', username=username))

    except Exception as e:
        logger.error(f"Signup error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Route for the login page
@app.route('/login')
def login_page():
    return render_template('login.html')


# Login handling route (POST)
@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = mongo.db.users.find_one({"username": username})

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            return jsonify({"error": "Invalid credentials"}), 401

        logger.info(f"User logged in: {username}")
        return redirect(url_for('chat', username=username))

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Route for the chat page
@app.route('/chat/<username>')
def chat(username):
    try:
        user = mongo.db.users.find_one({"username": username})
        if not user:
            logger.warning(f"Unauthorized access attempt by {username}")
            return redirect(url_for('login_page'))

        friends = user.get("friends", [])
        friend_requests = user.get("friend_requests", [])
        return render_template('chat.html', username=username, friends=friends, friend_requests=friend_requests)

    except Exception as e:
        logger.error(f"Chat page error for {username}: {e}")
        return redirect(url_for('login_page'))


# NEW ROUTE: Compiler page
@app.route('/compiler')
def compiler():
    username = request.args.get('username', '')
    return render_template('compiler.html', username=username)


# NEW ROUTE: Run code API endpoint
@app.route('/run_code', methods=['POST'])
def execute_code():
    code = request.form.get('code')
    language = request.form.get('language', 'python')

    print(f"Received code: {code[:50]}... (language: {language})")

    if not code:
        print("No code provided")
        return jsonify({"error": "Code is required"}), 400

    try:
        # Call your run_code function
        result = run_code(code, language)
        print(f"Function result: {result}")

        # Make sure we're returning JSON
        json_response = jsonify(result)
        print(f"Returning JSON response: {json_response}")
        return json_response
    except Exception as e:
        print(f"Error executing code: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Serve static files (CSS, JS, Images)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)


# Define common MIME types for better file handling
MIME_TYPES = {
    # Images
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'svg': 'image/svg+xml',
    'bmp': 'image/bmp',
    'ico': 'image/x-icon',
    'tiff': 'image/tiff',
    'tif': 'image/tiff',

    # Videos
    'mp4': 'video/mp4',
    'webm': 'video/webm',
    'mov': 'video/quicktime',
    'avi': 'video/x-msvideo',
    'wmv': 'video/x-ms-wmv',
    'flv': 'video/x-flv',
    'mkv': 'video/x-matroska',
    'mpeg': 'video/mpeg',
    'mpg': 'video/mpeg',
    '3gp': 'video/3gpp',

    # Audio
    'mp3': 'audio/mpeg',
    'wav': 'audio/wav',
    'ogg': 'audio/ogg',
    'aac': 'audio/aac',
    'm4a': 'audio/mp4',
    'flac': 'audio/flac',

    # Documents
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'txt': 'text/plain',
    'rtf': 'application/rtf',
    'csv': 'text/csv',

    # Archives
    'zip': 'application/zip',
    'rar': 'application/x-rar-compressed',
    '7z': 'application/x-7z-compressed',
    'tar': 'application/x-tar',
    'gz': 'application/gzip',

    # Others
    'json': 'application/json',
    'xml': 'application/xml',
    'js': 'text/javascript',
    'html': 'text/html',
    'css': 'text/css'
}


# Serve uploaded files
@app.route('/uploads/<filename>')
def serve_file(filename):
    try:
        # Get the full file path
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return "File not found", 404

        # Extract file extension
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''

        # Get file size
        file_size = os.path.getsize(file_path)
        print(f"Serving file: {filename}, size: {file_size} bytes")

        # Determine MIME type
        mime_type = MIME_TYPES.get(file_ext, 'application/octet-stream')

        # Special handling for videos and large files
        range_header = request.headers.get('Range', None)
        if range_header or mime_type.startswith('video/') or file_size > 5 * 1024 * 1024:  # 5MB threshold
            # Parse the range header if it exists
            byte1, byte2 = 0, None
            if range_header:
                print(f"Range request received: {range_header}")
                match = re.search(r'(\d+)-(\d*)', range_header)
                if match:
                    groups = match.groups()
                    if groups[0]: byte1 = int(groups[0])
                    if groups[1]: byte2 = int(groups[1])

            # If no end range specified, set to the end of the file
            if byte2 is None:
                byte2 = file_size - 1

            # Calculate content length
            length = min(byte2 - byte1 + 1, file_size - byte1)

            # Set up file reading with proper range
            def generate():
                with open(file_path, 'rb') as f:
                    f.seek(byte1)
                    remaining = length
                    chunk_size = 8192  # 8KB chunks

                    while remaining:
                        chunk = f.read(min(chunk_size, remaining))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk

            # Create response with proper headers
            response = app.response_class(
                generate(),
                mimetype=mime_type,
                status=206 if range_header else 200
            )

            # Add range headers
            response.headers.add('Content-Range', f'bytes {byte1}-{byte1 + length - 1}/{file_size}')
            response.headers.add('Accept-Ranges', 'bytes')
            response.headers.add('Content-Length', str(length))

            # Add cache control for better performance
            response.headers.add('Cache-Control', 'public, max-age=86400')  # Cache for a day

            return response
        else:
            # For smaller, non-streamable files - use send_file
            from flask import send_file
            return send_file(
                file_path,
                mimetype=mime_type,
                as_attachment=False,
                conditional=True
            )

    except Exception as e:
        print(f"ERROR in serve_file: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"Error serving file: {str(e)}", 500


# Handle new connections (SocketIO)
@socketio.on('connect')
def handle_connect():
    username = request.args.get('username')
    if username:
        online_users[username] = request.sid
        logger.info(f"User connected: {username}, Online users: {online_users}")

        # Fetch and send pending friend requests
        user = mongo.db.users.find_one({"username": username})
        if user:
            friend_requests = user.get("friend_requests", [])
            for sender in friend_requests:
                emit('receive_friend_request', {'sender': sender}, room=request.sid)

        emit('user_list', list(online_users.keys()), broadcast=True)


# Handle user disconnection (SocketIO)
@socketio.on('disconnect')
def handle_disconnect():
    for username, sid in list(online_users.items()):
        if sid == request.sid:
            del online_users[username]
            logger.info(f"User disconnected: {username}, Online users: {online_users}")
            emit('user_list', list(online_users.keys()), broadcast=True)
            break


# Handle fetching chat history (SocketIO)
@socketio.on('get_history')
def handle_get_history(data):
    sender = data['sender']
    recipient = data['recipient']
    messages = list(mongo.db.messages.find({
        "$or": [
            {"sender": sender, "recipient": recipient},
            {"sender": recipient, "recipient": sender}
        ]
    }).sort("timestamp", 1))

    voice_messages = list(mongo.db.voice_messages.find({
        "$or": [
            {"sender": sender, "recipient": recipient},
            {"sender": recipient, "recipient": sender}
        ]
    }).sort("timestamp", 1))

    file_messages = list(mongo.db.files.find({
        "$or": [
            {"sender": sender, "recipient": recipient},
            {"sender": recipient, "recipient": sender}
        ]
    }).sort("timestamp", 1))

    for msg in messages + voice_messages + file_messages:
        msg['_id'] = str(msg['_id'])

    emit('load_history', {
        'messages': messages,
        'voice_messages': voice_messages,
        'file_messages': file_messages
    }, room=request.sid)


# Handle sending messages (SocketIO)
@socketio.on('send_message')
def handle_message(data):
    sender = data['sender']
    recipient = data['recipient']
    message = data['message']

    mongo.db.messages.insert_one({
        "sender": sender,
        "recipient": recipient,
        "message": message,
        "timestamp": time.time()
    })

    if recipient in online_users:
        recipient_sid = online_users[recipient]
        emit('receive_message', {'sender': sender, 'message': message}, room=recipient_sid)


# Handle voice messages (SocketIO)
@socketio.on('send_voice_message')
def handle_voice_message(data):
    recipient = data['recipient']
    sender = data['sender']
    audio_blob = data['audio_blob']

    timestamp = str(int(time.time()))
    audio_filename = f"{sender}_{recipient}_{timestamp}.webm"
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)

    try:
        with open(audio_path, "wb") as audio_file:
            audio_file.write(base64.b64decode(audio_blob))

        audio_url = url_for('serve_file', filename=audio_filename, _external=True)

        mongo.db.voice_messages.insert_one({
            "sender": sender,
            "recipient": recipient,
            "audio_filename": audio_filename,
            "audio_url": audio_url,
            "timestamp": time.time()
        })

        if recipient in online_users:
            recipient_sid = online_users[recipient]
            emit('receive_voice_message', {'sender': sender, 'audio_url': audio_url}, room=recipient_sid)

    except Exception as e:
        print(f"Error saving audio message: {e}")
        emit('error', {'message': 'Error saving audio message.'}, room=request.sid)


# Handle file uploads (SocketIO)
# Replace the handle_file function in app.py
@socketio.on('send_file')
def handle_file(data):
    try:
        sender = data['sender']
        recipient = data['recipient']
        file_name = data['file_name']
        file_type = data['file_type']
        file_data = base64.b64decode(data['file_data'])
        loading_id = data.get('loading_id', None)  # Get the loading ID if provided

        # Add file size logging
        file_size = len(file_data)
        print(f"Processing file: {file_name}, Type: {file_type}, Size: {file_size} bytes")

        # Generate a unique filename to prevent collisions
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{sender}_{secure_filename(file_name)}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        # Save the file
        with open(file_path, 'wb') as f:
            f.write(file_data)

        # Create a URL for the file
        # Make sure we're using https if deployed in production
        server_name = request.host_url.rstrip('/')
        file_url = f"{server_name}/uploads/{unique_filename}"

        # Add special handling for video files
        is_video = file_type.startswith('video/')
        if is_video:
            print(f"VIDEO file detected: {file_name}, URL: {file_url}")

        # Store in database with file type information
        file_id = mongo.db.files.insert_one({
            "sender": sender,
            "recipient": recipient,
            "file_name": file_name,
            "file_type": file_type,
            "saved_filename": unique_filename,
            "file_url": file_url,
            "timestamp": timestamp,
            "file_size": file_size,
            "is_video": is_video
        }).inserted_id

        print(f"File saved: {file_path}, URL: {file_url}, Type: {file_type}")

        # Send to recipient if online
        if recipient in online_users:
            recipient_sid = online_users[recipient]
            print(f"Sending file notification to {recipient} (sid: {recipient_sid})")

            # Send metadata to recipient
            emit('receive_file', {
                'sender': sender,
                'file_name': file_name,
                'file_type': file_type,
                'file_url': file_url,
                'file_id': str(file_id),
                'is_video': is_video,
                'file_size': file_size
            }, room=recipient_sid)

        # Confirm success to sender, including the loading_id
        emit('file_sent', {
            'success': True,
            'file_name': file_name,
            'file_url': file_url,
            'file_type': file_type,
            'is_video': is_video,
            'loading_id': loading_id  # Include the loading ID in the response
        }, room=request.sid)

    except Exception as e:
        print(f"ERROR in handle_file: {str(e)}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': f'Error sending file: {str(e)}'}, room=request.sid)


# Search users route
@app.route('/search_users', methods=['POST'])
def search_users():
    try:
        query = request.form.get('query', '').strip()
        if not query:
            return jsonify({"users": []}), 200

        users = list(mongo.db.users.find(
            {"username": {"$regex": query, "$options": "i"}},
            {"username": 1, "_id": 0}
        ).limit(10))  # Limit results for performance

        return jsonify({"users": [user["username"] for user in users]}), 200

    except Exception as e:
        logger.error(f"Search users error: {e}")
        return jsonify({"error": "Error searching users"}), 500

# Send friend request route
@app.route('/send_friend_request', methods=['POST'])
def send_friend_request():
    try:
        sender = request.form.get('sender')
        recipient = request.form.get('recipient')

        if not sender or not recipient:
            return jsonify({"error": "Sender and recipient are required"}), 400

        if sender == recipient:
            return jsonify({"error": "Cannot send friend request to yourself"}), 400

        recipient_user = mongo.db.users.find_one({"username": recipient})
        if not recipient_user:
            return jsonify({"error": "User not found"}), 404

        sender_user = mongo.db.users.find_one({"username": sender})
        if not sender_user:
            return jsonify({"error": "Sender not found"}), 404

        if recipient in sender_user.get("friends", []):
            return jsonify({"error": "Already friends"}), 400

        if sender in recipient_user.get("friend_requests", []):
            return jsonify({"error": "Friend request already sent"}), 400

        mongo.db.users.update_one(
            {"username": recipient},
            {"$addToSet": {"friend_requests": sender}}
        )

        if recipient in online_users:
            recipient_sid = online_users[recipient]
            socketio.emit('receive_friend_request', {'sender': sender}, room=recipient_sid)

        logger.info(f"Friend request sent from {sender} to {recipient}")
        return jsonify({"message": "Friend request sent"}), 200

    except Exception as e:
        logger.error(f"Send friend request error: {e}")
        return jsonify({"error": "Error sending friend request"}), 500

# Accept friend request route
@app.route('/accept_friend_request', methods=['POST'])
def accept_friend_request():
    try:
        username = request.form.get('username')  # The user accepting the request
        sender = request.form.get('sender')      # The user who sent the request

        if not username or not sender:
            return jsonify({"error": "Username and sender are required"}), 400

        user = mongo.db.users.find_one({"username": username})
        sender_user = mongo.db.users.find_one({"username": sender})

        if not user or not sender_user:
            return jsonify({"error": "User not found"}), 404

        # Check if the sender actually sent a request
        if sender not in user.get("friend_requests", []):
            return jsonify({"error": "No friend request from this user"}), 400

        # Update both users: add each other to friends list and remove friend request
        mongo.db.users.update_one(
            {"username": username},
            {
                "$addToSet": {"friends": sender},
                "$pull": {"friend_requests": sender}
            }
        )

        mongo.db.users.update_one(
            {"username": sender},
            {
                "$addToSet": {"friends": username}
            }
        )

        # Notify sender if online
        if sender in online_users:
            sender_sid = online_users[sender]
            socketio.emit('friend_request_accepted', {'by': username}, room=sender_sid)

        logger.info(f"{username} accepted friend request from {sender}")
        return jsonify({"message": "Friend request accepted"}), 200

    except Exception as e:
        logger.error(f"Accept friend request error: {e}")
        return jsonify({"error": "Error accepting friend request"}), 500



# Reject friend request route
@app.route('/reject_friend_request', methods=['POST'])
def reject_friend_request():
    try:
        username = request.form.get('username')
        sender = request.form.get('sender')

        if not username or not sender:
            return jsonify({"error": "Username and sender are required"}), 400

        mongo.db.users.update_one(
            {"username": username},
            {"$pull": {"friend_requests": sender}}
        )

        logger.info(f"Friend request rejected: {username} rejected {sender}")
        return jsonify({"message": "Friend request rejected"}), 200

    except Exception as e:
        logger.error(f"Reject friend request error: {e}")
        return jsonify({"error": "Error rejecting friend request"}), 500


# Get friend requests route
@app.route('/get_friend_requests', methods=['POST'])
def get_friend_requests():
    try:
        username = request.form.get('username')
        if not username:
            return jsonify({"error": "Username is required"}), 400

        user = mongo.db.users.find_one({"username": username})
        if not user:
            return jsonify({"error": "User not found"}), 404

        friend_requests = user.get("friend_requests", [])
        return jsonify({"requests": friend_requests}), 200

    except Exception as e:
        logger.error(f"Get friend requests error: {e}")
        return jsonify({"error": "Error fetching friend requests"}), 500


# Optional: Chat history route (for REST API access, not used by SocketIO here)
@app.route('/chat_history/<username>/<recipient>', methods=['GET'])
def get_chat_history(username, recipient):
    messages = list(mongo.db.messages.find({
        "$or": [
            {"sender": username, "recipient": recipient},
            {"sender": recipient, "recipient": username}
        ]
    }).sort("timestamp", 1))

    voice_messages = list(mongo.db.voice_messages.find({
        "$or": [
            {"sender": username, "recipient": recipient},
            {"sender": recipient, "recipient": username}
        ]
    }).sort("timestamp", 1))

    file_messages = list(mongo.db.files.find({
        "$or": [
            {"sender": username, "recipient": recipient},
            {"sender": recipient, "recipient": username}
        ]
    }).sort("timestamp", 1))

    for msg in messages + voice_messages + file_messages:
        msg['_id'] = str(msg['_id'])

    return jsonify({
        "messages": messages,
        "voice_messages": voice_messages,
        "file_messages": file_messages
    })

@socketio.on('send_file_chunk')
def handle_file_chunk(data):
    try:
        sender = data['sender']
        recipient = data['recipient']
        file_name = data['file_name']
        file_type = data['file_type']
        file_data = base64.b64decode(data['file_data'])
        chunk_index = data['chunk_index']
        total_chunks = data['total_chunks']
        loading_id = data.get('loading_id')

        # Temporary chunk storage
        chunk_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{sender}_{recipient}_{file_name}')
        os.makedirs(chunk_dir, exist_ok=True)
        chunk_path = os.path.join(chunk_dir, f'chunk_{chunk_index}')
        with open(chunk_path, 'wb') as f:
            f.write(file_data)

        emit('chunk_received', {
            'chunk_index': chunk_index,
            'total_chunks': total_chunks,
            'file_name': file_name,
            'loading_id': loading_id
        }, room=request.sid)

        # Check if all chunks are received
        if chunk_index == total_chunks - 1:
            # Combine chunks
            timestamp = int(time.time())
            unique_filename = f"{timestamp}_{sender}_{secure_filename(file_name)}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            with open(file_path, 'wb') as f:
                for i in range(total_chunks):
                    chunk_path = os.path.join(chunk_dir, f'chunk_{i}')
                    with open(chunk_path, 'rb') as cf:
                        f.write(cf.read())

            # Clean up chunks
            import shutil
            shutil.rmtree(chunk_dir)

            file_size = os.path.getsize(file_path)
            server_name = request.host_url.rstrip('/')
            file_url = f"{server_name}/uploads/{unique_filename}"
            is_video = file_type.startswith('video/')
            file_id = mongo.db.files.insert_one({
                "sender": sender,
                "recipient": recipient,
                "file_name": file_name,
                "file_type": file_type,
                "saved_filename": unique_filename,
                "file_url": file_url,
                "timestamp": timestamp,
                "file_size": file_size,
                "is_video": is_video
            }).inserted_id

            if recipient in online_users:
                recipient_sid = online_users[recipient]
                emit('receive_file', {
                    'sender': sender,
                    'file_name': file_name,
                    'file_type': file_type,
                    'file_url': file_url,
                    'file_id': str(file_id),
                    'is_video': is_video,
                    'file_size': file_size
                }, room=recipient_sid)

            emit('file_sent', {
                'success': True,
                'file_name': file_name,
                'file_url': file_url,
                'file_type': file_type,
                'is_video': is_video,
                'loading_id': loading_id
            }, room=request.sid)

    except Exception as e:
        logger.error(f"Error in handle_file_chunk: {e}")
        emit('error', {'message': f'Error sending file chunk: {str(e)}'}, room=request.sid)


@socketio.on('search_messages')
def handle_search_messages(data):
    try:
        sender = data['sender']
        recipient = data['recipient']
        query = data['query'].strip()

        if not query:
            emit('search_results', {
                'messages': [],
                'voice_messages': [],
                'file_messages': []
            }, room=request.sid)
            return

        # Search text messages
        text_messages = list(mongo.db.messages.find({
            "$or": [
                {"sender": sender, "recipient": recipient},
                {"sender": recipient, "recipient": sender}
            ],
            "message": {"$regex": query, "$options": "i"}
        }).sort("timestamp", 1))

        # Include voice messages (not searchable by content, but included for context)
        voice_messages = list(mongo.db.voice_messages.find({
            "$or": [
                {"sender": sender, "recipient": recipient},
                {"sender": recipient, "recipient": sender}
            ]
        }).sort("timestamp", 1))

        # Search file messages by file_name
        file_messages = list(mongo.db.files.find({
            "$or": [
                {"sender": sender, "recipient": recipient},
                {"sender": recipient, "recipient": sender}
            ],
            "file_name": {"$regex": query, "$options": "i"}
        }).sort("timestamp", 1))

        # Convert ObjectId to string for JSON serialization
        for msg in text_messages + voice_messages + file_messages:
            msg['_id'] = str(msg['_id'])

        emit('search_results', {
            'messages': text_messages,
            'voice_messages': voice_messages,
            'file_messages': file_messages
        }, room=request.sid)

        logger.info(f"Search performed by {sender} for query '{query}' in chat with {recipient}")

    except Exception as e:
        logger.error(f"Search messages error: {e}")
        emit('error', {'message': 'Error searching messages'}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)