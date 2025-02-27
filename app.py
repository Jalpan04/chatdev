import base64
import os
import time
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] =  10 * 1024 * 1024 * 1024  # 10GB file limit

socketio = SocketIO(app)

online_users = {}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if username and email and password and confirm_password and password == confirm_password:
        return redirect(url_for('login_page'))

    return redirect(url_for('signup_page'))

# Route for the login page
@app.route('/login')
def login_page():
    return render_template('login.html')

# Login handling route (POST)
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username and password:
        return redirect(url_for('chat', username=username))

    return redirect(url_for('login_page'))

# Route for the chat page
@app.route('/chat/<username>')
def chat(username):
    return render_template('chat.html', username=username)

# Serve static files (CSS, JS, Images)
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

# Serve uploaded files
@app.route('/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Handle new connections (SocketIO)
@socketio.on('connect')
def handle_connect():
    username = request.args.get('username')
    if username:
        online_users[username] = request.sid
        print(f"Online users: {online_users}")
        emit('user_list', list(online_users.keys()), broadcast=True)

# Handle sending messages (SocketIO)
@socketio.on('send_message')
def handle_message(data):
    recipient = data['recipient']
    message = data['message']
    sender = data['sender']

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

        if recipient in online_users:
            recipient_sid = online_users[recipient]
            audio_url = url_for('serve_file', filename=audio_filename, _external=True)
            emit('receive_voice_message', {'sender': sender, 'audio_url': audio_url}, room=recipient_sid)

    except Exception as e:
        print(f"Error saving audio message: {e}")
        emit('error', {'message': 'Error saving audio message.'}, room=request.sid)


# Handle file uploads (Any file type)
@socketio.on('send_file')
def handle_file(data):
    sender = data['sender']
    recipient = data['recipient']
    file_name = data['file_name']
    file_type = data['file_type']
    file_data = data['file_data']



    if recipient in online_users:
        recipient_sid = online_users[recipient]
        emit('receive_file', {
            'sender': sender,
            'file_name': file_name,
            'file_type': file_type,
            'file_data': file_data
        }, room=recipient_sid)  # Send to the correct recipient
    else:
        emit('error', {'message': 'Recipient is not online.'}, room=request.sid)

# Handle user disconnection (SocketIO)
@socketio.on('disconnect')
def handle_disconnect():
    username = [user for user, sid in online_users.items() if sid == request.sid]
    if username:
        username = username[0]
        del online_users[username]
        emit('user_list', list(online_users.keys()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
