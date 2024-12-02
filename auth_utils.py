# auth_utils.py
import sqlite3
import hashlib
from config import DATABASE_PATH


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_database():
    """Initialize the SQLite database with necessary tables"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')

        # Check if default boss exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("Shammi Kapoor",))
        if cursor.fetchone()[0] == 0:
            # Add default boss if not exists
            default_password = hash_password("admin123")
            cursor.execute('''
            INSERT INTO users (username, password, role) 
            VALUES (?, ?, ?)
            ''', ("Shammi Kapoor", default_password, "boss"))

        conn.commit()


def load_users():
    """Load all users from the database"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, role FROM users")
        users = {row['username']: {
            'password': row['password'],
            'role': row['role']
        } for row in cursor.fetchall()}
    return users


def authenticate_user(username, password):
    """Authenticate user credentials"""
    hashed_password = hash_password(password)
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT role FROM users 
        WHERE username = ? AND password = ?
        ''', (username, hashed_password))
        result = cursor.fetchone()

    return (True, result[0]) if result else (False, None)


def add_user(username, password, role='member'):
    """Add a new user to the database"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            # Check if username already exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                return False

            # Insert new user
            hashed_pw = hash_password(password)
            cursor.execute('''
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            ''', (username, hashed_pw, role))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False