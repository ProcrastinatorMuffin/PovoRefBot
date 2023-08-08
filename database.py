# Standard library imports
import sqlite3
import logging
import pytz
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta

# Local application imports
from config import DB_NAME

# Configure logging for the database module
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler('database.log', maxBytes=5*1024*1024, backupCount=3)  # 5MB per log file, 3 backup logs
log_handler.setFormatter(log_formatter)

logger = logging.getLogger('database')
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

tokyo = pytz.timezone('Asia/Tokyo')

try:
    # Initialize SQLite database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    logger.info("Database connection initialized.")
except sqlite3.Error as e:
    logger.error(f"Error initializing database connection: {e}")


# Set up initial tables for the bot's database
# Attempt to create the 'codes' table if it doesn't already exist
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS codes (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    logger.info("'codes' table initialized or already exists.")
except sqlite3.Error as e:
    logger.error(f"Error initializing 'codes' table: {e}")

# Attempt to create the 'user_activity' table if it doesn't already exist
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            referral_code TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    logger.info("'user_activity' table initialized or already exists.")
except sqlite3.Error as e:
    logger.error(f"Error initializing 'user_activity' table: {e}")


def current_time_in_tokyo():
    """
    Get the current date and time in the Tokyo timezone.

    Returns:
        datetime: Current datetime object in Tokyo's timezone.
    """
    return datetime.now(tokyo)


def add_code(code: str):
    """
    Add a new referral code to the database.

    Args:
        code (str): The referral code to be added.
    """
    try:
        cursor.execute('INSERT INTO codes (code) VALUES (?)', (code,))
        conn.commit()
        logger.info(f"Added new referral code: {code}")
    except sqlite3.Error as e:
        logger.error(f"Error adding referral code {code}: {e}")


def get_codes():
    """
    Retrieve all referral codes from the database.

    Returns:
        list: A list of tuples containing referral code information.
    """
    try:
        cursor.execute('SELECT * FROM codes')
        codes = cursor.fetchall()
        logger.info("Successfully fetched all referral codes.")
        return codes
    except sqlite3.Error as e:
        logger.error(f"Error fetching referral codes: {e}")
        return []


def delete_code(id: int):
    """
    Delete a referral code from the database by its ID.

    Args:
        id (int): The ID of the referral code to be deleted.
    """
    try:
        cursor.execute('DELETE FROM codes WHERE id = ?', (id,))
        conn.commit()
        logger.info(f"Successfully deleted referral code with ID: {id}.")
    except sqlite3.Error as e:
        logger.error(f"Error deleting referral code with ID {id}: {e}")


def increment_code_usage(id: int):
    """
    Increment the usage count of a referral code by its ID.

    Args:
        id (int): The ID of the referral code whose usage count needs to be incremented.
    """
    try:
        cursor.execute('UPDATE codes SET usage_count = usage_count + 1 WHERE id = ?', (id,))
        conn.commit()
        logger.info(f"Incremented usage count for referral code with ID: {id}.")
    except sqlite3.Error as e:
        logger.error(f"Error incrementing usage count for referral code with ID {id}: {e}")


def code_exists(code: str) -> bool:
    """
    Check if the given referral code already exists in the database.

    Args:
        code (str): The referral code to check for existence.

    Returns:
        bool: True if the code exists, otherwise False.
    """
    try:
        cursor.execute('SELECT * FROM codes WHERE code = ?', (code,))
        exists = cursor.fetchone() is not None
        logger.info(f"Checked existence of referral code: {code}. Exists: {exists}.")
        return exists
    except sqlite3.Error as e:
        logger.error(f"Error checking existence of referral code {code}: {e}")
        return False


def log_user_activity(user_id: int, action: str, referral_code: str = None) -> None:
    """
    Logs the user's activity in the database.

    Args:
        user_id (int): The ID of the user.
        action (str): The action performed by the user (e.g., "add", "get").
        referral_code (str, optional): The referral code associated with the action.

    Returns:
        None
    """
    try:
        current_time = current_time_in_tokyo().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'INSERT INTO user_activity (user_id, action, referral_code, timestamp) VALUES (?, ?, ?, ?)',
            (user_id, action, referral_code, current_time)
        )
        conn.commit()
        logger.info(f"Logged user activity: UserID {user_id}, Action {action}, Referral Code {referral_code}, Timestamp {current_time}.")
    except sqlite3.Error as e:
        logger.error(f"Error logging user activity for UserID {user_id}, Action {action}, Referral Code {referral_code}: {e}")


def can_add_code(user_id: int, referral_code: str) -> bool:
    """
    Checks if the user can add the given referral code.

    Args:
        user_id (int): The ID of the user.
        referral_code (str): The referral code the user wants to add.

    Returns:
        bool: True if the user can add the referral code, False otherwise.
    """
    try:
        cursor.execute(
            'SELECT 1 FROM user_activity WHERE user_id = ? AND action = "add" AND referral_code = ? LIMIT 1',
            (user_id, referral_code)
        )
        return cursor.fetchone() is None
    except sqlite3.Error as e:
        logger.error(f"Error checking if user (UserID {user_id}) can add referral code {referral_code}: {e}")
        return False


def can_get_code(user_id: int) -> bool:
    """
    Checks if the user can retrieve a referral code based on rate limits.

    Args:
        user_id (int): The ID of the user.

    Returns:
        bool: True if the user can retrieve a referral code, False otherwise.
    """
    one_hour_ago = (current_time_in_tokyo() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
    try:
        cursor.execute(
            'SELECT 1 FROM user_activity WHERE user_id = ? AND action = "get" AND timestamp > ? LIMIT 1',
            (user_id, one_hour_ago)
        )
        return cursor.fetchone() is None
    except sqlite3.Error as e:
        logger.error(f"Error checking if user (UserID {user_id}) can get a referral code: {e}")
        return False

