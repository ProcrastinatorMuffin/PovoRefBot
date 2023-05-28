import sqlite3
from config import DB_NAME

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