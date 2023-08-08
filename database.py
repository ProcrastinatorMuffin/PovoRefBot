import sqlite3
from config import DB_NAME
from datetime import datetime, timedelta

# Initialize SQLite database
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS codes (
        id INTEGER PRIMARY KEY,
        code TEXT NOT NULL,
        usage_count INTEGER DEFAULT 0
    )
''')
conn.commit()

cursor.execute('''
    CREATE TABLE user_activity (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        referral_code TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
''')
conn.commit()


def add_code(code: str):
    cursor.execute('INSERT INTO codes (code) VALUES (?)', (code,))
    conn.commit()


def get_codes():
    cursor.execute('SELECT * FROM codes')
    return cursor.fetchall()


def delete_code(id: int):
    cursor.execute('DELETE FROM codes WHERE id = ?', (id,))
    conn.commit()


def increment_code_usage(id: int):
    cursor.execute('UPDATE codes SET usage_count = usage_count + 1 WHERE id = ?', (id,))
    conn.commit()


def code_exists(code: str):
    cursor.execute('SELECT * FROM codes WHERE code = ?', (code,))
    return cursor.fetchone() is not None


def log_user_activity(user_id, action, referral_code=None):
    """Logs the user's activity in the database."""
    cursor.execute(
        'INSERT INTO user_activity (user_id, action, referral_code) VALUES (?, ?, ?)',
        (user_id, action, referral_code)
    )
    conn.commit()


def can_add_code(user_id, referral_code):
    """Checks if the user can add the given referral code."""
    # Check if the user has already added this referral code
    cursor.execute(
        'SELECT * FROM user_activity WHERE user_id = ? AND action = "add" AND referral_code = ?',
        (user_id, referral_code)
    )
    if cursor.fetchone():
        return False
    return True


def can_get_code(user_id):
    """Checks if the user can retrieve a referral code."""
    one_hour_ago = datetime.now() - timedelta(hours=1)
    cursor.execute(
        'SELECT * FROM user_activity WHERE user_id = ? AND action = "get" AND timestamp > ?',
        (user_id, one_hour_ago)
    )
    if cursor.fetchone():
        return False
    return True
