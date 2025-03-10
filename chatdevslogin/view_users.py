import sqlite3

DATABASE = "users.db"


def view_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()

    for user in users:
        print(user)


if __name__ == "__main__":
    view_users()
