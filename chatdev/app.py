import base64
import os
import time
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

online_users = {}

# Directories for uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Directory to save voice messages
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    # Retrieve the username, email, password, and confirm_password from the form
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    # Check if all fields are provided and passwords match
    if username and email and password and confirm_password and password == confirm_password:
        # Redirect to the login page after successful signup
        return redirect(url_for('login_page'))

    # If validation fails, redirect back to the signup page
    return redirect(url_for('signup_page'))

# Route for the login page
@app.route('/login')
def login_page():
    return render_template('login.html')

# Login handling route (POST)
@app.route('/login', methods=['POST'])
def login():
    # Retrieve the username and password from the form
    username = request.form.get('username')
    password = request.form.get('password')

    # Check if both username and password are provided
    if username and password:
        # Redirect to chat page with the username
        return redirect(url_for('chat', username=username))

    # If either is missing, redirect back to the login page
    return redirect(url_for('login_page'))

# Route for the chat page
@app.route('/chat/<username>')
def chat(username):
    return render_template('chat.html', username=username)


# Serve static files (CSS, JS, Images) from the 'static' folder
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)


# Serve uploaded audio files
@app.route('/uploads/<filename>')
def serve_audio(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Handle new connections (SocketIO)
@socketio.on('connect')
def handle_connect():
    username = request.args.get('username')
    if username:
        online_users[username] = request.sid  # Store the session ID for the user
        # Broadcast the updated user list
        emit('user_list', list(online_users.keys()), broadcast=True)

# Handle sending messages (SocketIO)
@socketio.on('send_message')
def handle_message(data):
    recipient = data['recipient']
    message = data['message']
    sender = data['sender']

    # Ensure the recipient exists in the online users
    if recipient in online_users:
        recipient_sid = online_users[recipient]
        emit('receive_message', {'sender': sender, 'message': message}, room=recipient_sid)

# Handle sending voice messages (SocketIO)
@socketio.on('send_voice_message')
def handle_voice_message(data):
    recipient = data['recipient']
    sender = data['sender']
    audio_blob = data['audio_blob']

    # Use a timestamp to create a unique filename for each audio message
    timestamp = str(int(time.time()))
    audio_filename = f"{sender}_{recipient}_{timestamp}.webm"
    audio_path = os.path.join(UPLOAD_FOLDER, audio_filename)

    try:
        # Decode the base64 audio data and save it as a file
        with open(audio_path, "wb") as audio_file:
            audio_file.write(base64.b64decode(audio_blob))

        # Ensure the recipient is connected
        if recipient in online_users:
            recipient_sid = online_users[recipient]
            audio_url = url_for('serve_audio', filename=audio_filename, _external=True)
            emit('receive_voice_message', {'sender': sender, 'audio_url': audio_url}, room=recipient_sid)

    except Exception as e:
        print(f"Error saving audio message: {e}")
        emit('error', {'message': 'Error saving audio message.'}, room=request.sid)


#Handle file upload
@socketio.on('send_file')
def handle_file_upload(data):
    recipient = data['recipient']
    sender = data['sender']
    file_name = data['file_name']
    file_blob = data['file_blob']

    timestamp = str(int(time.time()))
    file_path = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{file_name}")

    try:
        # Save the file to the uploads directory
        with open(file_path, "wb") as file:
            file.write(base64.b64decode(file_blob))

        file_url = url_for('serve_file', filename=f"{timestamp}_{file_name}", _external=True)

        if recipient in online_users:
            emit('receive_file', {'sender': sender, 'file_name': file_name, 'file_url': file_url}, room=online_users[recipient])

    except Exception as e:
        print(f"Error saving file: {e}")
        emit('error', {'message': 'Error saving file.'}, room=request.sid)

# Handle user disconnection (SocketIO)
@socketio.on('disconnect')
def handle_disconnect():
    # Find the username associated with the current session ID
    username = [user for user, sid in online_users.items() if sid == request.sid]
    if username:
        username = username[0]
        del online_users[username]
        emit('user_list', list(online_users.keys()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
