import mysql.connector
import bcrypt

# MySQL connection configuration
DB_CONFIG = {
   "host": "sql12.freesqldatabase.com",
    "user": "sql12752715",  # Replace with your MySQL username
    "password": "please wait",  # Replace with your MySQL password
    "database": "sql12752715"  # Name of your MySQL database

def create_database():
    """
    Ensure the database exists before proceeding.
    """
    connection = mysql.connector.connect(
        host=DB_CONFIG["host"],  # Corrected this line
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(DB_CONFIG["database"]))  # Use the correct DB name
    connection.commit()  # Commit the creation of the database
    cursor.close()
    connection.close()
    print("Database created or verified successfully.")

def setup_tables():
    """
    Create tables and insert initial data.
    """
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Create 'users' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_admin TINYINT(1) DEFAULT 0,
    is_master_agent TINYINT(1) DEFAULT 0,
    is_super_agent TINYINT(1) DEFAULT 0,
    is_user_agent TINYINT(1) DEFAULT 1,  -- Default to user role
    is_blocked TINYINT(1) DEFAULT 0,
    referred_by INT DEFAULT NULL,
    referral_code VARCHAR(255) UNIQUE DEFAULT NULL,
    commission_percentage FLOAT DEFAULT 0.0,
    is_deposit_enabled TINYINT(1) DEFAULT 1,
    is_withdraw_enabled TINYINT(1) DEFAULT 1,
    FOREIGN KEY (referred_by) REFERENCES users(id)
    );
    """)
    print("Table 'users' created or verified successfully.")

    # Create 'balance_history' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS balance_history (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        type ENUM('deposit', 'withdrawal') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    print("Table 'balance_history' created or verified successfully.")

    # Create 'banking_requests' table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS banking_requests (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        amount DECIMAL(10, 2) NOT NULL,
        request_type ENUM('deposit', 'withdrawal') NOT NULL,
        status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
        reason TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    print("Table 'banking_requests' created or verified successfully.")

    # Insert an admin account for testing purposes
    admin_password = bcrypt.hashpw("Admin@123".encode("utf-8"), bcrypt.gensalt()).decode()
    cursor.execute("""
    INSERT IGNORE INTO users (username, password, is_admin) 
    VALUES (%s, %s, TRUE);
    """, ('admin', admin_password))
    print("Admin account created or verified successfully.")

    # Insert a super agent account for testing purposes
    super_agent_password = bcrypt.hashpw("Karim@2024".encode("utf-8"), bcrypt.gensalt()).decode()
    cursor.execute("""
    INSERT IGNORE INTO users (username, password, is_super_agent) 
    VALUES (%s, %s, TRUE);
    """, ('superagent1', super_agent_password))
    print("Super agent account created or verified successfully.")

    connection.commit()
    cursor.close()
    connection.close()
    print("Database setup completed successfully!")

if __name__ == "__main__":
    create_database()
    setup_tables()
