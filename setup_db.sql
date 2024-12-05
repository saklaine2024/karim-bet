-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0,           -- 1 if admin
    is_master_agent INTEGER DEFAULT 0,    -- 1 if master agent
    is_super_agent INTEGER DEFAULT 0,     -- 1 if super agent
    is_user_agent INTEGER DEFAULT 0,      -- 1 if user agent
    referred_by INTEGER,                  -- Referring agent ID (null if no referral)
    referral_code TEXT UNIQUE,            -- Unique referral code
    FOREIGN KEY(referred_by) REFERENCES users(id)
);

-- Create balance history table
CREATE TABLE IF NOT EXISTS balance_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    type TEXT CHECK(type IN ('deposit', 'withdrawal')),  -- Type can either be 'deposit' or 'withdrawal'
    transaction_id TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Create sample user and set roles (optional)
INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent, referral_code) 
VALUES 
    ('admin', '$2b$12$UP5crfE.Djrt6Dd6j0KxTuR3sjxfffiHaiOgJqLXar167qP83I3CK', 1, 0, 0, 0, 'ADMIN123'),
    ('masteragent1', '$2b$12$yfsExXniNA5yqQ5UGn0pJeuUTExut7ZA4E7QSx43yM2jPZ26i46Mi', 0, 1, 0, 0, 'MASTER123'),
    ('superagent1', '$2b$12$UP5crfE.Djrt6Dd6j0KxTuR3sjxfffiHaiOgJqLXar167qP83I3CK', 0, 0, 1, 0, 'SUPER123');

-- Optionally, you can insert a sample balance history (this is just an example, remove if not needed)
INSERT INTO balance_history (user_id, amount, type, transaction_id) 
VALUES
    (1, 500, 'deposit', 'TRX001'),
    (2, 200, 'withdrawal', 'TRX002');
