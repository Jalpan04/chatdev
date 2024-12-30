from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)

online_users = {}

# Route for the login page
@app.route('/')
def index():
    return render_template('login.html')

# Route to handle user login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    if username:
        return redirect(url_for('chat', username=username))  # Redirect to chat page with the username
    return redirect(url_for('index'))  # Redirect back to login if no username provided

# Route for the chat page
@app.route('/chat/<username>')
def chat(username):
    return render_template('chat.html', username=username)

# Serve the CSS for login
@app.route('/login.css')
def serve_login_css():
    return send_from_directory('.', 'login.css')

# Serve the CSS for chat
@app.route('/styles.css')
def serve_chat_css():
    return send_from_directory('.', 'styles.css')

# Serve the JavaScript for chat
@app.route('/script.js')
def serve_script():
    return send_from_directory('.', 'chat.js')

# Handle new connections
@socketio.on('connect')
def handle_connect():
    username = request.args.get('username')
    if username:
        online_users[username] = request.sid
        # Broadcast the updated user list
        emit('user_list', list(online_users.keys()), broadcast=True)

# Handle sending messages
@socketio.on('send_message')
def handle_message(data):
    recipient = data['recipient']
    message = data['message']
    sender = data['sender']
    if recipient in online_users:
        emit('receive_message', {'sender': sender, 'message': message}, room=online_users[recipient])

# Handle user disconnection
@socketio.on('disconnect')
def handle_disconnect():
    username = [user for user, sid in online_users.items() if sid == request.sid]
    if username:
        username = username[0]
        del online_users[username]
        emit('user_list', list(online_users.keys()), broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
