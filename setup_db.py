import sqlite3
import os

# Define the path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), "db", "system.db")

# Create the database directory if it doesn't exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Connect to the database
connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Create the 'users' table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    is_master_agent INTEGER DEFAULT 0,
    is_super_agent INTEGER DEFAULT 0,
    is_user_agent INTEGER DEFAULT 1
);
""")

# Create the 'balance_history' table
cursor.execute("""
CREATE TABLE IF NOT EXISTS balance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
""")

# Create the 'banking_requests' table
cursor.execute("""
CREATE TABLE IF NOT EXISTS banking_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    request_type TEXT NOT NULL CHECK (request_type IN ('deposit', 'withdrawal')),
    status TEXT NOT NULL DEFAULT 'pending',
    reason TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
""")

# Insert an admin account for testing purposes
# Replace 'hashed_password' with an actual hashed password
import bcrypt
admin_password = bcrypt.hashpw("Admin@123".encode("utf-8"), bcrypt.gensalt()).decode()
cursor.execute("""
INSERT OR IGNORE INTO users (username, password, is_admin) 
VALUES ('admin', ?, 1);
""", (admin_password,))

# Insert a master agent account for testing purposes
master_agent_password = bcrypt.hashpw("Karim@2024".encode("utf-8"), bcrypt.gensalt()).decode()
cursor.execute("""
INSERT OR IGNORE INTO users (username, password, is_master_agent) 
VALUES ('masteragent1', ?, 1);
""", (master_agent_password,))

# Commit changes and close the connection
connection.commit()
connection.close()

print("Database setup completed successfully!")
