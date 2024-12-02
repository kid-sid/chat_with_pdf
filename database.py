import sqlite3
import bcrypt

DB_FILE = "users.db"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        FOREIGN KEY(username) REFERENCES users(username)
    )
    ''')


    conn.commit()
    conn.close()

# Signup a new user
def signup_user(username, password):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

# Login an existing user
def login_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
        return True
    return False

def save_user_query(username, question, answer):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO user_queries (username, question, answer)
    VALUES (?, ?, ?)
    ''', (username, question, answer))
    
    conn.commit()
    conn.close()

def get_user_queries(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT question, answer FROM user_queries
    WHERE username = ?
    ''', (username,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

