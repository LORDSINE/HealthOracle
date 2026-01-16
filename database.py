"""Database configuration and helper functions."""

import sqlite3

DATABASE = 'healthoracle.db'

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with schema."""
    conn = get_db()
    
    # Check if we need to migrate from patient_id to user_id
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if the table has patient_id column (old schema)
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'patient_id' in columns and 'user_id' not in columns:
            # Migrate from patient_id to user_id
            print("Migrating database schema from patient_id to user_id...")
            conn.execute('ALTER TABLE users RENAME COLUMN patient_id TO user_id')
            conn.commit()
    else:
        # Create new table with user_id
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT
            )
        ''')
        conn.commit()
    
    conn.close()

def get_next_user_id():
    """Generate next user_id in sequence P0001, P0002, etc."""
    conn = get_db()
    cursor = conn.execute('SELECT MAX(CAST(SUBSTR(user_id, 2) AS INTEGER)) as max_id FROM users WHERE user_id LIKE "P%"')
    result = cursor.fetchone()
    conn.close()
    
    max_id = result['max_id'] if result and result['max_id'] else 0
    next_id = max_id + 1
    return f"P{next_id:04d}"

def get_user_by_id(user_id):
    """Get user information by user_id."""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    """Get user information by email."""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user

def create_user(user_id, password_hash, name, email, phone=None):
    """Create a new user in the database."""
    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO users (user_id, password_hash, name, email, phone) VALUES (?, ?, ?, ?, ?)',
            (user_id, password_hash, name, email, phone)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e

def update_password(user_id, password_hash):
    """Update user password."""
    conn = get_db()
    conn.execute('UPDATE users SET password_hash = ? WHERE user_id = ?', (password_hash, user_id))
    conn.commit()
    conn.close()
