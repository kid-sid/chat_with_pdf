import sqlite3
import bcrypt

DB_FILE = "users.db"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create or update the users table with the api_key column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            api_key TEXT  -- Add api_key column
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
        cursor.execute("INSERT INTO users (username, password, api_key) VALUES (?, ?, NULL)", (username, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


# Save the API key
def save_api_key(username, api_key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Ensure the users table has the api_key column
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'api_key' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN api_key TEXT")
    
    cursor.execute("UPDATE users SET api_key = ? WHERE username = ?", (api_key, username))
    conn.commit()
    conn.close()

def get_api_key(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT api_key FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]  # Return the API key if found
    return None  # Return None if no API key is associated


# Login an existing user
def login_user(username, password, api_key):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Fetch the user's hashed password
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
        # If password matches, save/update the API key
        cursor.execute("UPDATE users SET api_key = ? WHERE username = ?", (api_key, username))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def save_user_query(username, question, answer):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO user_queries (username, question, answer)
    VALUES (?, ?, ?)
    ''', (username, question, answer))
    
    conn.commit()
    conn.close()

def get_user_queries(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT question, answer FROM user_queries
    WHERE username = ?
    ''', (username,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows
