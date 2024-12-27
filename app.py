from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app)

# Store online users and their session ids
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

# Handle new connections
@socketio.on('connect')
def handle_connect():
    # Get the username from the query string
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
    if recipient in online_users:
        emit('receive_message', {'sender': data['sender'], 'message': message}, room=online_users[recipient])

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
