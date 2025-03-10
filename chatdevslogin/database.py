from flask import Flask, render_template, request, redirect, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Used for session management

DATABASE = "users.db"

# Function to initialize the database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)''')
        conn.commit()

# Function to get database connection
def get_db():
    conn = getattr(g, '_database', None)
    if conn is None:
        conn = g._database = sqlite3.connect(DATABASE)
    return conn

# Close database connection when app stops
@app.teardown_appcontext
def close_connection(exception):
    conn = getattr(g, '_database', None)
    if conn is not None:
        conn.close()

# Home route (redirects to login)
@app.route('/')
def home():
    return redirect('/login')

# Sign-Up Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']

        if password != confirm_password:
            return "Passwords do not match!", 400

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                           (username, email, password))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "Username or email already taken!", 400

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            session['user'] = user[1]  # Storing username in session
            return redirect('/dashboard')
        else:
            return "Invalid credentials!", 401

    return render_template('login.html')

# Protected Dashboard Route
@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html', username=session['user'])
    return redirect('/login')

# Delete Account Route
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user' in session:
        username = session['user']

        conn = get_db()
        cursor = conn.cursor()

        # Delete user from database
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()

        # Log the user out after deletion
        session.pop('user', None)

        return redirect('/signup')  # Redirect to sign-up page after account deletion

    return redirect('/login')  # Redirect to login if user is not logged in


# Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# Run the app
if __name__ == '__main__':
    init_db()  # Initialize database before running the app
    app.run(debug=True)
