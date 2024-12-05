from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'

DB_PATH = "db/db/system.db"

# Helper function to connect to the database
def connect_db():
    return sqlite3.connect(DB_PATH)

# Helper function to get user roles
def get_user_roles(user_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT is_admin, is_master_agent, is_super_agent, is_user_agent FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    if user:
        return {
            "is_admin": user[0],
            "is_master_agent": user[1],
            "is_super_agent": user[2],
            "is_user_agent": user[3],
        }
    return {}

# Helper function to hash passwords
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Helper function to check passwords
def check_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)

# Helper function to get balance
def get_balance(user_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT SUM(amount) FROM balance_history WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    connection.close()
    return balance if balance else 0

# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to sign up
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Username or password cannot be empty!", "error")
            return render_template('signup.html')

        hashed_password = hash_password(password)

        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent) VALUES (?, ?, ?, ?, ?, ?)",
                (username, hashed_password, 0, 0, 0, 1)  # Default as User Agent
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
                'user_agent'
            )
            flash(f"Signed in as {session['role'].replace('_', ' ').capitalize()}!", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid username or password", "error")
    return render_template('signin.html')

# Route to log out
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

# Role-based dashboard redirection
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
    elif role == 'user_agent':
        return redirect(url_for('user_dashboard'))
    else:
        flash("Access denied.", "error")
        return redirect(url_for('signin'))

# Route for admin panel
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        hashed_password = hash_password(password)

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

    cursor.execute("SELECT id, username, is_admin, is_master_agent, is_super_agent, is_user_agent FROM users")
    users = cursor.fetchall()
    connection.close()

    return render_template('admin_panel.html', users=users)

# Route for Master Agent's Dashboard
@app.route('/master_dashboard')
def master_dashboard():
    if 'user_id' in session and session.get('role') == 'master_agent':
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE is_master_agent = 0")  # Fetch all non-master agents
        agents = cursor.fetchall()
        connection.close()
        return render_template('master_dashboard.html', agents=agents)
    flash("Access denied! Only Master Agents can view this page.", "error")
    return redirect(url_for('signin'))

# Route for banking page
@app.route('/banking', methods=['GET', 'POST'])
def banking():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    user_id = session['user_id']
    balance = get_balance(user_id)

    if request.method == 'POST' and 'view_balance' in request.form:
        balance = get_balance(user_id)

    return render_template('banking.html', balance=balance)

# Route to approve banking requests (Master Agents only)
@app.route('/admin/approve_request/<int:request_id>')
def approve_request(request_id):
    if 'user_id' in session and session.get('role') == 'master_agent':
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM banking_requests WHERE id = ?", (request_id,))
        request = cursor.fetchone()

        if request:
            user_id = request[1]
            amount = request[3]
            request_type = request[4]

            if request_type == 'deposit':
                record_transaction(user_id, amount, 'deposit')
            elif request_type == 'withdrawal':
                if get_balance(user_id) >= amount:
                    record_transaction(user_id, -amount, 'withdrawal')
                else:
                    flash("Insufficient funds for withdrawal request.", "error")
                    return redirect(url_for('admin_panel'))

            cursor.execute("UPDATE banking_requests SET status = 'approved' WHERE id = ?", (request_id,))
            connection.commit()

        connection.close()
        flash("Request approved successfully!", "success")
        return redirect(url_for('admin_panel'))
    flash("You are not authorized to approve requests.", "error")
    return redirect(url_for('signin'))

# Helper function to record a transaction
def record_transaction(user_id, amount, trans_type):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO balance_history (user_id, amount, type) VALUES (?, ?, ?)", (user_id, amount, trans_type))
    connection.commit()
    connection.close()

if __name__ == '__main__':
    app.run(debug=True)
