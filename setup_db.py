import sqlite3
import os

# Define the database path relative to this script's location
DB_PATH = os.path.join("db", "db", "system.db")

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Create the users table with roles
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL, -- master_agent, super_agent, user_agent, user
    parent_id INTEGER, -- Refers to the parent agent ID
    commission_rate REAL DEFAULT 0, -- Commission rate for agents
    FOREIGN KEY (parent_id) REFERENCES users(id)
);
""")

# Create the balance history table
cursor.execute("""
CREATE TABLE IF NOT EXISTS balance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL, -- e.g., deposit, bet, win, loss
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# Create the banking requests table
cursor.execute("""
CREATE TABLE IF NOT EXISTS banking_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    request_type TEXT NOT NULL,  -- 'deposit' or 'withdrawal'
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    reason TEXT,  -- Optional reason for rejection
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")


# Create the users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);
""")

# Create the balance_history table
cursor.execute("""
CREATE TABLE IF NOT EXISTS balance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# Create the banking_requests table
cursor.execute("""
CREATE TABLE IF NOT EXISTS banking_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    request_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    reason TEXT DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

connection.commit()
connection.close()

print(f"Database setup completed. Tables created in {DB_PATH}")
