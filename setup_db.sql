-- Drop the existing table if it exists
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,
    is_master_agent INTEGER DEFAULT 0,
    is_super_agent INTEGER DEFAULT 0,
    is_user_agent INTEGER DEFAULT 0,
    is_blocked INTEGER DEFAULT 0,
    referred_by INTEGER,
    referral_code TEXT UNIQUE,
    commission_percentage REAL DEFAULT 0.0,  -- Commission percentage for agents
    is_deposit_enabled INTEGER DEFAULT 1,     -- Enable deposit (1 = yes, 0 = no)
    is_withdraw_enabled INTEGER DEFAULT 1,    -- Enable withdrawal (1 = yes, 0 = no)
    commission_withdraw_status TEXT DEFAULT 'pending', -- Commission withdrawal status
    FOREIGN KEY (referred_by) REFERENCES users (id)
);

-- Create balance history table
CREATE TABLE IF NOT EXISTS balance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    type TEXT,   -- 'deposit' or 'withdrawal'
    status TEXT DEFAULT 'pending',
    transaction_id TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Create commission withdrawal requests table
CREATE TABLE IF NOT EXISTS commission_withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Create banking requests table
CREATE TABLE IF NOT EXISTS banking_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    method TEXT NOT NULL,
    transaction_id TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Create sample users (admin, master agent, super agent) and set roles
INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent, referral_code) 
VALUES 
    ('admin', '$2b$12$UP5crfE.Djrt6Dd6j0KxTuR3sjxfffiHaiOgJqLXar167qP83I3CK', 1, 0, 0, 0, 'ADMIN123'),
    ('masteragent1', '$2b$12$yfsExXniNA5yqQ5UGn0pJeuUTExut7ZA4E7QSx43yM2jPZ26i46Mi', 0, 1, 0, 0, 'MASTER123'),
    ('superagent1', '$2b$12$UP5crfE.Djrt6Dd6j0KxTuR3sjxfffiHaiOgJqLXar167qP83I3CK', 0, 0, 1, 0, 'SUPER123');

-- Add a table to track user commissions
CREATE TABLE IF NOT EXISTS user_commissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    commission_percentage REAL DEFAULT 0.0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Create commission withdrawal requests table
CREATE TABLE IF NOT EXISTS commission_withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Ensure columns for deposit, withdraw, and commission are not duplicated
-- Columns should already be added in the previous step, so we skip this step

-- If there are any existing entries, remove duplicates in referral_code if they exist
-- This step ensures there is no conflict with UNIQUE constraint
UPDATE users
SET referral_code = 'new_unique_code' 
WHERE referral_code IS NULL;

-- Ensure there are no duplicate referral codes
SELECT referral_code, COUNT(*) 
FROM users 
GROUP BY referral_code 
HAVING COUNT(*) > 1;
