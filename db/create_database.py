import sqlite3

# Connect to the database (it will be created if it doesn't exist)
connection = sqlite3.connect("db/system.db")
cursor = connection.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);
""")

# Create balance history table
cursor.execute("""
CREATE TABLE IF NOT EXISTS balance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL, -- e.g., deposit, cost, profit/loss
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

# Create banking_requests table (new)
cursor.execute("""
CREATE TABLE IF NOT EXISTS banking_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_type TEXT NOT NULL,  -- 'deposit' or 'withdrawal'
    amount REAL NOT NULL,
    transaction_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    reason TEXT,  -- Optional reason for rejection
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
""")

print("Database and tables created successfully.")

# Commit changes and close connection
connection.commit()
connection.close()
