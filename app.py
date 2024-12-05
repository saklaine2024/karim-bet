from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'

DB_PATH = os.path.join(os.getcwd(), "db", "system.db")

# Helper function to connect to the database
def connect_db():
    return sqlite3.connect(DB_PATH)

# Helper function to get user roles
def get_user_roles(user_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT is_admin, is_master_agent, is_super_agent, is_user_agent, is_blocked FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    if user:
        return {
            "is_admin": user[0],
            "is_master_agent": user[1],
            "is_super_agent": user[2],
            "is_user_agent": user[3],
            "is_blocked": user[4]
        }
    return {}

# Helper function to hash passwords
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Helper function to check passwords
def check_password(stored_password, provided_password):
    if isinstance(stored_password, str):
        stored_password = stored_password.encode('utf-8')
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

# Helper function to get balance and live monitoring details
def get_user_details(user_id):
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT SUM(amount) FROM balance_history WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM balance_history WHERE user_id = ? AND amount < 0", (user_id,))
    exposure = cursor.fetchone()[0] or 0

    cursor.execute("SELECT * FROM balance_history WHERE user_id = ?", (user_id,))
    live_activity = cursor.fetchall()

    connection.close()
    return balance, exposure, live_activity

# Route for homepage
@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_panel'))
        elif role == 'master_agent':
            return redirect(url_for('master_dashboard'))
        elif role == 'super_agent':
            return redirect(url_for('super_agent_dashboard'))
        elif role == 'user':
            return redirect(url_for('index'))

    return render_template('index.html')

# Route to sign up (with referral code)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        referral_code = request.form.get('referral_code')

        if not username or not password:
            flash("Username or password cannot be empty!", "error")
            return render_template('signup.html')

        hashed_password = hash_password(password)

        referred_by = None
        if referral_code:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM users WHERE referral_code = ?", (referral_code,))
            referred_by = cursor.fetchone()
            connection.close()

            if not referred_by:
                flash("Invalid referral code.", "error")
                return render_template('signup.html')
            referred_by = referred_by[0]  # Set the referring agent's ID

        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent, referred_by) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, hashed_password, 0, 0, 0, 1, referred_by)  # Default as User
            )
            connection.commit()
            connection.close()

            flash("User created successfully!", "success")
            return redirect(url_for('signin'))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")
    return render_template('signup.html')

# Route to sign in
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        connection.close()

        if user and check_password(user[2], password):  # Check password (index 2 is password)
            session['user_id'] = user[0]
            session['role'] = (
                'admin' if user[3] else
                'master_agent' if user[4] else
                'super_agent' if user[5] else
                'user'
            )
            session['is_blocked'] = user[6]
            flash(f"Signed in as {session['role'].replace('_', ' ').capitalize()}!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid username or password", "error")
    return render_template('signin.html')

# Route for dashboard (redirect based on role)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please sign in to access the dashboard.", "error")
        return redirect(url_for('signin'))

    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin_panel'))
    elif role == 'master_agent':
        return redirect(url_for('master_dashboard'))
    elif role == 'super_agent':
        return redirect(url_for('super_agent_dashboard'))
    elif role == 'user':
        return redirect(url_for('index'))
    else:
        flash("Access denied.", "error")
        return redirect(url_for('signin'))

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    session.pop('role', None)  # Remove role from session
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))  # Redirect to the index page after logout

# Admin panel route
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    search_query = request.args.get('search', '')  # Get search query
    if search_query:
        cursor.execute("SELECT * FROM users WHERE username LIKE ?", ('%' + search_query + '%',))
    else:
        cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM balance_history")
    total_balance = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM balance_history WHERE amount < 0")
    total_exposure = cursor.fetchone()[0] or 0

    connection.close()

    # Handle form submission for creating a user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = hash_password(password)

        # Role assignment based on selected role
        is_master_agent = 1 if role == "master_agent" else 0
        is_super_agent = 1 if role == "super_agent" else 0
        is_user_agent = 1 if role == "user_agent" else 0

        try:
            cursor.execute(
                "INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent) VALUES (?, ?, ?, ?, ?, ?)",
                (username, hashed_password, 0, is_master_agent, is_super_agent, is_user_agent)
            )
            connection.commit()
            flash(f"{role.replace('_', ' ').capitalize()} created successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")

    return render_template('admin_panel.html', users=users, total_balance=total_balance, total_exposure=total_exposure)

# Admin approval/rejection of deposit/withdrawal
@app.route('/admin/approve_transaction/<int:transaction_id>/<action>', methods=['GET', 'POST'])
def approve_transaction(transaction_id, action):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM balance_history WHERE id = ?", (transaction_id,))
    transaction = cursor.fetchone()

    if transaction:
        if action == 'approve':
            cursor.execute("UPDATE balance_history SET status = 'approved' WHERE id = ?", (transaction_id,))
            connection.commit()
            flash("Transaction approved successfully.", "success")
        elif action == 'reject':
            cursor.execute("UPDATE balance_history SET status = 'rejected' WHERE id = ?", (transaction_id,))
            connection.commit()
            flash("Transaction rejected.", "error")

    connection.close()
    return redirect(url_for('admin_panel'))

# Block/Unblock users (Admin and agents)
@app.route('/admin/block_user/<int:user_id>/<action>', methods=['GET', 'POST'])
def block_user(user_id, action):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    if action == 'block':
        cursor.execute("UPDATE users SET is_blocked = 1 WHERE id = ?", (user_id,))
        flash("User has been blocked.", "success")
    elif action == 'unblock':
        cursor.execute("UPDATE users SET is_blocked = 0 WHERE id = ?", (user_id,))
        flash("User has been unblocked.", "success")

    connection.commit()
    connection.close()
    return redirect(url_for('admin_panel'))

# Admin settings route (password change)
@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only!", "error")
        return redirect(url_for('signin'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user = cursor.fetchone()
        connection.close()

        if user and check_password(user[2], current_password):  # Check if current password is correct
            hashed_password = hash_password(new_password)

            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed_password, session['user_id']))
            connection.commit()
            connection.close()

            flash("Password changed successfully!", "success")
        else:
            flash("Incorrect current password", "error")

    return render_template('admin_settings.html')

# Helper function to record a transaction
def record_transaction(user_id, amount, trans_type):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO balance_history (user_id, amount, type) VALUES (?, ?, ?)", (user_id, amount, trans_type))
    connection.commit()
    connection.close()

if __name__ == '__main__':
    app.run(debug=True)
