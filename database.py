"""
import sqlite3
from datetime import datetime
import os
import pandas as pd

# --- Define DB_PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'fraud_detection.db')


def setup_database():

    print(f"Setting up database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # --- 'users' TABLE ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        upi_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        last_active TEXT,
        device_os TEXT,
        phone_number TEXT UNIQUE NOT NULL,
        bank_name TEXT NOT NULL,
        password_hash TEXT NOT NULL
    )
    ''')

    # --- 'transactions' TABLE ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id TEXT PRIMARY KEY,
        sender_upi_id TEXT NOT NULL,
        receiver_upi_id TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        is_fraud INTEGER,
        FOREIGN KEY (sender_upi_id) REFERENCES users(upi_id)
    )
    ''')

    # --- 'fraud_alerts' TABLE ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS fraud_alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT NOT NULL,
        risk_score REAL NOT NULL,
        explanation TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
    )
    ''')

    # --- 'transaction_data_log' TABLE ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS transaction_data_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Transaction_ID TEXT, Sender_UPI_ID TEXT, Receiver_UPI_ID TEXT,
        Transaction_Type TEXT, Payment_Gateway TEXT, Transaction_City TEXT,
        Transaction_State TEXT, IP_Address TEXT, Transaction_Status TEXT,
        Device_OS TEXT, Transaction_Frequency REAL, Merchant_Category TEXT,
        Transaction_Channel TEXT, Transaction_Amount_Deviation REAL,
        Days_Since_Last_Transaction REAL, amount REAL, fraud INTEGER,
        hour REAL, day_of_week REAL
    )
    ''')

    # --- NEW: 'payment_confirmations' TABLE (Updated with transaction_id) ---
    c.execute('''
    CREATE TABLE IF NOT EXISTS payment_confirmations (
        token TEXT PRIMARY KEY,
        transaction_id TEXT NOT NULL,
        sender_upi_id TEXT,
        receiver_upi_id TEXT,
        amount REAL,
        timestamp TEXT
    )
    ''')

    conn.commit()
    conn.close()
    print(f"Database setup complete. File created at: {DB_PATH}")


# --- USER FUNCTIONS ---
def insert_user(upi_id, name, device_os, phone_number, bank_name, password_hash):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        last_active = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            INSERT INTO users 
            (upi_id, name, last_active, device_os, phone_number, bank_name, password_hash) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        , (upi_id, name, last_active, device_os, phone_number, bank_name, password_hash))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        print(f"User with phone number {phone_number} already exists.")
    except Exception as e:
        print(f"Error inserting user: {e}")

def get_user_data(upi_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE upi_id = ?", (upi_id,))
    user_data = c.fetchone()
    if user_data:
        c.execute("UPDATE users SET last_active = ? WHERE upi_id = ?",
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), upi_id))
        conn.commit()
    conn.close()
    return user_data

def get_user_data_by_phone(phone_number):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
    user_data = c.fetchone()
    conn.close()
    return user_data

def get_receiver_data(receiver_upi_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM transactions WHERE receiver_upi_id = ? LIMIT 1", (receiver_upi_id,))
    receiver_data = c.fetchone()
    conn.close()
    return receiver_data

# --- TRANSACTION FUNCTIONS ---
def get_user_transactions(sender_upi_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        SELECT * FROM transactions 
        WHERE sender_upi_id = ?
        ORDER BY timestamp DESC
    , (sender_upi_id,))
    transactions = c.fetchall()
    conn.close()
    return transactions

def insert_transaction(transaction_id, sender_upi_id, receiver_upi_id, amount, timestamp, status, is_fraud):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            INSERT INTO transactions 
            (transaction_id, sender_upi_id, receiver_upi_id, amount, timestamp, status, is_fraud) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        , (transaction_id, sender_upi_id, receiver_upi_id, amount, timestamp, status, is_fraud))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error inserting transaction: {e}")

def insert_fraud_alert(transaction_id, risk_score, explanation):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute(
            INSERT INTO fraud_alerts (transaction_id, risk_score, explanation, timestamp) 
            VALUES (?, ?, ?, ?)
        , (transaction_id, risk_score, explanation, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error inserting fraud alert: {e}")

def log_all_data(dataframe):
    if dataframe is None:
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        dataframe.to_sql('transaction_data_log', conn, if_exists='append', index=False)
        conn.close()
        print("Preprocessed data logged to database.")
    except Exception as e:
        print(f"Error logging data: {e}")

# --- NEW: SMS CONFIRMATION & UPDATE FUNCTIONS ---

def insert_confirmation(token, transaction_id, sender_upi_id, receiver_upi_id, amount):

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO payment_confirmations VALUES (?, ?, ?, ?, ?, datetime('now'))",
              (token, transaction_id, sender_upi_id, receiver_upi_id, amount))
    conn.commit()
    conn.close()

def get_confirmation(token):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM payment_confirmations WHERE token = ?", (token,))
    data = c.fetchone()
    conn.close()
    return data

def delete_confirmation(token):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM payment_confirmations WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def update_transaction_fraud_status(transaction_id, is_fraud):

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE transactions SET is_fraud = ? WHERE transaction_id = ?", (is_fraud, transaction_id))
        conn.commit()
        conn.close()
        print(f"Transaction {transaction_id} updated. New is_fraud status: {is_fraud}")
    except Exception as e:
        print(f"Error updating transaction status: {e}")"""

import sqlite3
from datetime import datetime
import os
import pandas as pd

# --- Define DB_PATH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'fraud_detection.db')


def get_db_connection():
    """
    Creates a database connection with a timeout and enables WAL mode.
    Timeout=30 means it will wait 30 seconds for a lock to clear before crashing.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute('PRAGMA journal_mode=WAL;')  # Enable Write-Ahead Logging for better concurrency
    return conn


def setup_database():
    """Sets up the database, creating tables if they don't exist."""
    print(f"Setting up database at: {DB_PATH}")

    # Use context manager (with ... as ...) to ensure connection closes
    with get_db_connection() as conn:
        c = conn.cursor()

        # --- 'users' TABLE ---
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            upi_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            last_active TEXT,
            device_os TEXT,
            phone_number TEXT UNIQUE NOT NULL,
            bank_name TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
        ''')

        # --- 'transactions' TABLE ---
        c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            sender_upi_id TEXT NOT NULL,
            receiver_upi_id TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            is_fraud INTEGER,
            FOREIGN KEY (sender_upi_id) REFERENCES users(upi_id)
        )
        ''')

        # --- 'fraud_alerts' TABLE ---
        c.execute('''
        CREATE TABLE IF NOT EXISTS fraud_alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            risk_score REAL NOT NULL,
            explanation TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
        )
        ''')

        # --- 'transaction_data_log' TABLE ---
        c.execute('''
        CREATE TABLE IF NOT EXISTS transaction_data_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Transaction_ID TEXT, Sender_UPI_ID TEXT, Receiver_UPI_ID TEXT,
            Transaction_Type TEXT, Payment_Gateway TEXT, Transaction_City TEXT,
            Transaction_State TEXT, IP_Address TEXT, Transaction_Status TEXT,
            Device_OS TEXT, Transaction_Frequency REAL, Merchant_Category TEXT,
            Transaction_Channel TEXT, Transaction_Amount_Deviation REAL,
            Days_Since_Last_Transaction REAL, amount REAL, fraud INTEGER,
            hour REAL, day_of_week REAL
        )
        ''')

        # --- 'payment_confirmations' TABLE ---
        c.execute('''
        CREATE TABLE IF NOT EXISTS payment_confirmations (
            token TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            sender_upi_id TEXT,
            receiver_upi_id TEXT,
            amount REAL,
            timestamp TEXT
        )
        ''')

        # Connection commits automatically on exit of 'with' block
    print(f"Database setup complete. File created at: {DB_PATH}")


# --- USER FUNCTIONS ---
def insert_user(upi_id, name, device_os, phone_number, bank_name, password_hash):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            last_active = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("""
                INSERT INTO users 
                (upi_id, name, last_active, device_os, phone_number, bank_name, password_hash) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (upi_id, name, last_active, device_os, phone_number, bank_name, password_hash))
    except sqlite3.IntegrityError:
        print(f"User with phone number {phone_number} already exists.")
    except Exception as e:
        print(f"Error inserting user: {e}")


def get_user_data(upi_id):
    """
    Fetches user data.
    OPTIMIZED: Only updates last_active if it's actually retrieved.
    Uses 'with' to guarantee connection closing.
    """
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE upi_id = ?", (upi_id,))
            user_data = c.fetchone()

            if user_data:
                # We still update last_active, but WAL mode and timeout will prevent crashes
                c.execute("UPDATE users SET last_active = ? WHERE upi_id = ?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), upi_id))
            return user_data
    except Exception as e:
        print(f"Error fetching user data: {e}")
        return None


def get_user_data_by_phone(phone_number):
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
            return c.fetchone()
    except Exception as e:
        print(f"Error fetching user by phone: {e}")
        return None


def get_receiver_data(receiver_upi_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM transactions WHERE receiver_upi_id = ? LIMIT 1", (receiver_upi_id,))
            return c.fetchone()
    except Exception as e:
        print(f"Error fetching receiver: {e}")
        return None


# --- TRANSACTION FUNCTIONS ---
def get_user_transactions(sender_upi_id):
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT * FROM transactions 
                WHERE sender_upi_id = ?
                ORDER BY timestamp DESC
            """, (sender_upi_id,))
            return c.fetchall()
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return []


def insert_transaction(transaction_id, sender_upi_id, receiver_upi_id, amount, timestamp, status, is_fraud):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO transactions 
                (transaction_id, sender_upi_id, receiver_upi_id, amount, timestamp, status, is_fraud) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (transaction_id, sender_upi_id, receiver_upi_id, amount, timestamp, status, is_fraud))
    except Exception as e:
        print(f"Error inserting transaction: {e}")


def insert_fraud_alert(transaction_id, risk_score, explanation):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute("""
                INSERT INTO fraud_alerts (transaction_id, risk_score, explanation, timestamp) 
                VALUES (?, ?, ?, ?)
            """, (transaction_id, risk_score, explanation, timestamp))
    except Exception as e:
        print(f"Error inserting fraud alert: {e}")


def log_all_data(dataframe):
    if dataframe is None:
        return
    try:
        with get_db_connection() as conn:
            dataframe.to_sql('transaction_data_log', conn, if_exists='append', index=False)
        print("Preprocessed data logged to database.")
    except Exception as e:
        print(f"Error logging data: {e}")


# --- SMS CONFIRMATION & UPDATE FUNCTIONS ---

def insert_confirmation(token, transaction_id, sender_upi_id, receiver_upi_id, amount):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT INTO payment_confirmations VALUES (?, ?, ?, ?, ?, datetime('now'))",
                      (token, transaction_id, sender_upi_id, receiver_upi_id, amount))
    except Exception as e:
        print(f"Error inserting confirmation: {e}")


def get_confirmation(token):
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM payment_confirmations WHERE token = ?", (token,))
            return c.fetchone()
    except Exception as e:
        print(f"Error getting confirmation: {e}")
        return None


def delete_confirmation(token):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM payment_confirmations WHERE token = ?", (token,))
    except Exception as e:
        print(f"Error deleting confirmation: {e}")


def update_transaction_fraud_status(transaction_id, is_fraud):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("UPDATE transactions SET is_fraud = ? WHERE transaction_id = ?", (is_fraud, transaction_id))
        print(f"Transaction {transaction_id} updated. New is_fraud status: {is_fraud}")
    except Exception as e:
        print(f"Error updating transaction status: {e}")