from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt
import os
import uuid  # For generating unique codes

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'

DB_CONFIG = {
    "host": "localhost",
    "user": "root",  # Replace with your MySQL username
    "password": "Shemu2024",  # Replace with your MySQL password
    "database": "system_db"  # Name of your MySQL database
}

# Generate a unique referral code
def generate_referral_code():
    return str(uuid.uuid4())[:8]  # Create a random 8-character string

# Helper function to connect to the database
def connect_db():
    connection = mysql.connector.connect(**DB_CONFIG)
    return connection

# Helper function to get user roles
def get_user_roles(user_id):
    connection = connect_db()
    cursor = connection.cursor()
    cursor.execute("SELECT is_admin, is_master_agent, is_super_agent, is_user_agent, is_blocked FROM users WHERE id = %s", (user_id,))
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
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode()
    return hashed_password

# Helper function to check passwords
def check_password(stored_password, provided_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

# Create super agent via Master Agent
@app.route('/create_super_agent', methods=['GET', 'POST'])
def create_super_agent():
    if 'user_id' not in session or session.get('role') != 'master_agent':
        flash("Access denied. Master Agents only!", "error")
        return redirect(url_for('signin'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        commission_percentage = request.form['commission_percentage']

        hashed_password = hash_password(password)

        # Create the super agent in the database
        connection = connect_db()
        cursor = connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password, is_super_agent, commission_percentage, referred_by) VALUES (%s, %s, 1, %s, %s)",
                (username, hashed_password, commission_percentage, session['user_id'])
            )
            connection.commit()
            flash("Super Agent created successfully!", "success")
            return redirect(url_for('master_dashboard'))  # Redirect back to the master dashboard
        except mysql.connector.IntegrityError:
            flash("Username already exists!", "error")
        finally:
            connection.close()

    return render_template('create_super_agent.html')  # Return the form to create a super agent

# Route for view activity
@app.route('/view_activity/<int:user_id>', methods=['GET'])
def view_activity(user_id):
    if 'user_id' not in session:
        flash("Please sign in to view activity.", "error")
        return redirect(url_for('signin'))

    # Only authorized roles can view activities
    role = session.get('role')
    if role not in ['admin', 'master_agent', 'super_agent']:
        flash("Access denied.", "error")
        return redirect(url_for('dashboard'))

    # Ensure query fetches `username` through a JOIN if needed
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 
            user_activity.id, 
            user_activity.activity_type, 
            user_activity.amount, 
            user_activity.created_at, 
            users.username
        FROM 
            user_activity
        JOIN 
            users 
        ON 
            user_activity.user_id = users.id
        WHERE 
            user_activity.user_id = %s;
    """, (user_id,))
    activities = cursor.fetchall()
    connection.close()

    return render_template('view_activity.html', activities=activities, user_id=user_id)

# Route for homepage (start here)
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
            return render_template('index.html', user_logged_in=True)
    return render_template('index.html', user_logged_in=False)

#Route to Master Dashboard
@app.route('/master_dashboard')
def master_dashboard():
    if 'user_id' not in session or session.get('role') != 'master_agent':
        flash("Access denied. Master Agents only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    # Fetch agents and users for the master agent
    cursor.execute("""
        SELECT id, username, is_master_agent, is_super_agent, is_user_agent 
        FROM users WHERE referred_by = %s
    """, (session['user_id'],))
    agents_and_users = cursor.fetchall()

    connection.close()
    return render_template('master_dashboard.html', agents_and_users=agents_and_users)

# Route to Super Agent
@app.route('/super_agent_dashboard', methods=['GET', 'POST'])
def super_agent_dashboard():
    if 'user_id' not in session or session.get('role') != 'super_agent':
        flash("Access denied. Super Agents only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    # Fetch the User Agents referred by the current Super Agent
    cursor.execute("""
        SELECT u.id, u.username, u.balance, u.commission_percentage, u.referral_code
        FROM users u
        WHERE u.referred_by = %s AND u.is_user_agent = 1
    """, (session['user_id'],))
    user_agents = cursor.fetchall()

    # Handle form submission for creating a User Agent
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        commission_percentage = request.form.get('commission_percentage')

        # Hash the password
        hashed_password = hash_password(password)

        try:
            referral_code = generate_referral_code()  # Generate a unique referral code
            cursor.execute("""
                INSERT INTO users (username, password, is_user_agent, referred_by, commission_percentage, referral_code)
                VALUES (%s, %s, 1, %s, %s, %s)
            """, (username, hashed_password, session['user_id'], commission_percentage, referral_code))
            connection.commit()
            flash("User Agent created successfully!", "success")
        except mysql.connector.IntegrityError:
            flash("Username already exists!", "error")

    connection.close()
    return render_template('super_dashboard.html', user_agents=user_agents)

# Route to User Agent
# User_Agent dashboard
@app.route('/user_agent_dashboard', methods=['GET'])
def user_agent_dashboard():
    if 'user_id' not in session or session.get('role') != 'user_agent':
        flash("Access denied. User Agents only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    # Fetch user details and referral code for the User Agent
    cursor.execute("""
        SELECT u.username, u.commission_percentage, u.referral_code,
        (SELECT SUM(amount) FROM user_activity WHERE referred_by = u.id) AS total_activity,
        (SELECT SUM(balance) FROM users WHERE referred_by = u.id) AS total_balance
        FROM users u WHERE u.id = %s
    """, (session['user_id'],))
    user_agent_details = cursor.fetchone()

    # Fetch user activities referred by the User Agent
    cursor.execute("""
        SELECT ua.id, ua.activity_type, ua.amount, ua.timestamp 
        FROM user_activity ua
        WHERE ua.referred_by = %s
        ORDER BY ua.timestamp DESC
    """, (session['user_id'],))
    user_activities = cursor.fetchall()

    connection.close()
    return render_template(
        'user_agent_dashboard.html',
        user_agent_details=user_agent_details,
        user_activities=user_activities
    )

# Route to sign up (with referral code)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        referral_code = request.form.get('referral_code')

        # Validate username and password
        if not username or not password:
            flash("Username or password cannot be empty!", "error")
            return render_template('signup.html')

        # Hash the password
        hashed_password = hash_password(password)

        # Check if referral code is valid and get the user agent id
        referred_by = None
        if referral_code:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("SELECT id FROM users WHERE referral_code = %s AND is_user_agent = 1", (referral_code,))
            referred_by = cursor.fetchone()
            connection.close()

            if not referred_by:
                flash("Invalid referral code.", "error")
                return render_template('signup.html')
            referred_by = referred_by[0]  # Assign referring user's ID

        # Create a new user with the referred_by field pointing to the user agent's ID
        try:
            referral_code = os.urandom(8).hex()  # Generate a random referral code
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent, is_blocked, referred_by, referral_code)
                VALUES (%s, %s, 0, 0, 0, 1, 0, %s, %s)
                """,
                (username, hashed_password, referred_by, referral_code)  # setting roles explicitly
            )
            connection.commit()
            connection.close()

            flash("User account created successfully!", "success")
            return redirect(url_for('signin'))
        except mysql.connector.IntegrityError:
            flash("Username already exists!", "error")
            return render_template('signup.html')

    return render_template('signup.html')

# Banking route where users can request deposits/withdrawals
@app.route('/banking', methods=['GET', 'POST'])
def banking():
    if 'user_id' not in session:
        flash("Please sign in to access banking.", "error")
        return redirect(url_for('signin'))

    user_id = session['user_id']
    connection = connect_db()
    cursor = connection.cursor()

    if request.method == 'POST':
        amount = request.form['amount']
        request_type = request.form.get('action')  # 'action' is now used for POST data (Deposit or Withdraw)

        # Validate that a request type is selected
        if not request_type:
            flash("Please select a request type (Deposit or Withdrawal).", "error")
            return redirect(url_for('banking'))  # Redirect back to the banking page if request_type is missing

        # Validate amount
        if not amount or float(amount) <= 0:
            flash("Please enter a valid amount.", "error")
            return redirect(url_for('banking'))  # Redirect back to the banking page if amount is invalid

        # Insert banking request (deposit/withdrawal)
        cursor.execute(""" 
        INSERT INTO banking_requests (user_id, amount, request_type) 
        VALUES (%s, %s, %s)
        """, (user_id, amount, request_type))
        connection.commit()

        flash(f"{request_type.capitalize()} request has been submitted!", "success")

    # Fetch the user's banking requests
    cursor.execute("SELECT * FROM banking_requests WHERE user_id = %s", (user_id,))
    banking_requests = cursor.fetchall()

    connection.close()
    return render_template('banking.html', banking_requests=banking_requests)

# Route to sign in
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
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

            flash(f"Signed in as {session['role'].replace('_', ' ').capitalize()}!", "success")
            return redirect(url_for('index'))

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
    elif role == 'user_agent':
        return redirect(url_for('user_agent_dashboard'))
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
        cursor.execute("SELECT * FROM users WHERE username LIKE %s", ('%' + search_query + '%',))
    else:
        cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM balance_history")
    total_balance = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM balance_history WHERE amount < 0")
    total_exposure = cursor.fetchone()[0] or 0

    # Handle form submission for creating an agent
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        commission_percentage = request.form['commission_percentage']

        hashed_password = hash_password(password)

        # Role assignment based on selected role
        is_master_agent = 1 if role == "master_agent" else 0
        is_super_agent = 1 if role == "super_agent" else 0
        is_user_agent = 1 if role == "user_agent" else 0

        try:
            cursor.execute(
                "INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent, commission_percentage) VALUES (%s, %s, 0, %s, %s, %s, %s)",
                (username, hashed_password, is_master_agent, is_super_agent, is_user_agent, commission_percentage)
            )
            connection.commit()
            flash(f"{role.replace('_', ' ').capitalize()} created successfully!", "success")
        except mysql.connector.IntegrityError:
            flash("Username already exists!", "error")

    connection.close()

    return render_template('admin_panel.html', users=users, total_balance=total_balance, total_exposure=total_exposure)

# Admin approval/rejection of deposit/withdrawal
@app.route('/admin/approve_transaction/<int:transaction_id>/<action>', methods=['GET', 'POST'])
def approve_transaction(transaction_id, action):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM banking_requests WHERE id = %s", (transaction_id,))
    transaction = cursor.fetchone()

    if transaction:
        if action == 'approve':
            cursor.execute("UPDATE banking_requests SET status = 'approved' WHERE id = %s", (transaction_id,))
            connection.commit()
            flash("Transaction approved successfully.", "success")
        elif action == 'reject':
            cursor.execute("UPDATE banking_requests SET status = 'rejected' WHERE id = %s", (transaction_id,))
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
        cursor.execute("UPDATE users SET is_blocked = 1 WHERE id = %s", (user_id,))
        flash("User has been blocked.", "success")
    elif action == 'unblock':
        cursor.execute("UPDATE users SET is_blocked = 0 WHERE id = %s", (user_id,))
        flash("User has been unblocked.", "success")

    connection.commit()
    connection.close()
    return redirect(url_for('admin_panel'))

# Delete user/agent account
@app.route('/admin/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Access denied. Admins only!", "error")
        return redirect(url_for('signin'))

    connection = connect_db()
    cursor = connection.cursor()

    try:
        # Delete user/agent from users table
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        connection.commit()
        flash("User/Agent deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", "error")
        connection.rollback()
    finally:
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
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        connection.close()

        if user and check_password(user[2], current_password):  # Check if current password is correct
            hashed_password = hash_password(new_password)

            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, session['user_id']))
            connection.commit()
            connection.close()

            flash("Password changed successfully!", "success")
        else:
            flash("Incorrect current password", "error")

    return render_template('admin_settings.html')


if __name__ == '__main__':
    app.run(debug=True)
