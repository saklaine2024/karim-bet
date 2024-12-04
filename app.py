from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key'  # Change this to something unique

DB_PATH = "db/db/system.db"

# Helper function to check if the user is an admin, master agent, super agent, or user agent
def get_user_roles(user_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT is_admin, is_master_agent, is_super_agent, is_user_agent FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    if user:
        is_admin = user[0] == 1
        is_master_agent = user[1] == 1
        is_super_agent = user[2] == 1
        is_user_agent = user[3] == 1
        return is_admin, is_master_agent, is_super_agent, is_user_agent
    return False, False, False, False  # Default return if no user found

# Helper function to get balance
def get_balance(user_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT SUM(amount) FROM balance_history WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    connection.close()
    return balance if balance else 0

# Helper function to hash passwords securely
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

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
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, password, is_admin, is_master_agent, is_super_agent, is_user_agent) VALUES (?, ?, ?, ?, ?, ?)", 
                           (username, hashed_password, 0, 0, 0, 1))  # Default as User Agent
            connection.commit()
            connection.close()

            flash("User created successfully!", "success")
            return redirect(url_for('signin'))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
    return render_template('signup.html')

# Route to create a Master Agent (can be done through admin route)
@app.route('/admin/create_master_agent', methods=['GET', 'POST'])
def create_master_agent():
    if 'user_id' in session and is_admin(session['user_id']):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            hashed_password = hash_password(password)

            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, password, is_master_agent) VALUES (?, ?, ?)", 
                           (username, hashed_password, 1))  # is_master_agent = 1 for master agents
            connection.commit()
            connection.close()

            flash("Master Agent created successfully!", "success")
            return redirect(url_for('master_dashboard'))

        return render_template('create_master_agent.html')  # Render a form to create a master agent
    else:
        return redirect(url_for('index'))


# Route to sign in
# Route to sign in
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = hash_password(password)

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        connection.close()

        if user:
            # Check if the user is a Master Agent, Super Agent, or User Agent
            if user[4] == 1:  # Assuming 'is_master_agent' is the 5th column (index 4)
                session['user_id'] = user[0]  # Store user ID in session
                session['role'] = 'master_agent'
                flash("Signed in as Master Agent!", "success")
                return redirect(url_for('master_dashboard'))  # Redirect to master agent dashboard

            elif user[5] == 1:  # Assuming 'is_super_agent' is the 6th column (index 5)
                session['user_id'] = user[0]  # Store user ID in session
                session['role'] = 'super_agent'
                flash("Signed in as Super Agent!", "success")
                return redirect(url_for('super_agent_dashboard'))  # Redirect to super agent dashboard

            elif user[6] == 1:  # Assuming 'is_user_agent' is the 7th column (index 6)
                session['user_id'] = user[0]  # Store user ID in session
                session['role'] = 'user_agent'
                flash("Signed in as User Agent!", "success")
                return redirect(url_for('user_agent_dashboard'))  # Redirect to user agent dashboard

            else:
                flash("You don't have the necessary permissions", "error")
        else:
            flash("Invalid username or password", "error")
    return render_template('signin.html')


# Route for Master Agent's Dashboard (Admin Panel)
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session:
        # Check if the logged-in user is a master agent
        user_id = session['user_id']
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT is_master_agent FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        connection.close()

        if user and user[0] == 1:  # Check if the user is a master agent
            # Fetch relevant data for the master agent (e.g., list of agents, requests, etc.)
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE is_master_agent = 0")  # Fetch all users who are not master agents
            agents = cursor.fetchall()
            connection.close()

            # Use 'master_dashboard.html' as the template
            return render_template('master_dashboard.html', agents=agents)  # Pass the agents list to the template
        else:
            flash("Access denied! Only Master Agents can view this page.", "error")
            return redirect(url_for('signin'))  # Redirect to signin page if not a master agent

    return redirect(url_for('signin'))  # Redirect to signin if not logged in


# Route for banking page
@app.route('/banking', methods=['GET', 'POST'])
def banking():
    if 'user_id' not in session:
        return redirect(url_for('signin'))  # Redirect to signin if not logged in

    user_id = session['user_id']
    balance = 0  # Default is 0

    # Check if user requested to view balance
    if request.method == 'POST' and 'view_balance' in request.form:
        balance = get_balance(user_id)  # Get the balance when the button is clicked

    return render_template('banking.html', balance=balance)

# Route for admin to view pending requests
@app.route('/admin/requests')
def admin_requests():
    if 'user_id' in session:
        is_admin, is_master_agent, is_super_agent, is_user_agent = get_user_roles(session['user_id'])
        if is_master_agent:  # Only allow Master Agents to view and approve requests
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM banking_requests WHERE status = 'pending'")
            requests = cursor.fetchall()
            connection.close()
            return render_template('admin_requests.html', requests=requests)
        else:
            flash("You are not authorized to access this page.", "error")
            return redirect(url_for('index'))
    return redirect(url_for('signin'))

# Route to approve requests
@app.route('/admin/approve_request/<int:request_id>')
def approve_request(request_id):
    if 'user_id' in session:
        is_admin, is_master_agent, is_super_agent, is_user_agent = get_user_roles(session['user_id'])
        if is_master_agent:  # Only Master Agents can approve requests
            connection = sqlite3.connect(DB_PATH)
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
                        return redirect(url_for('admin_requests'))

                cursor.execute("UPDATE banking_requests SET status = ?, reason = ? WHERE id = ?",
                               ('approved', '', request_id))
                connection.commit()

            connection.close()
            flash("Request approved successfully!", "success")
            return redirect(url_for('admin_requests'))
        else:
            flash("You are not authorized to approve requests.", "error")
            return redirect(url_for('index'))
    return redirect(url_for('signin'))

# Helper function to record a transaction
def record_transaction(user_id, amount, trans_type):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO balance_history (user_id, amount, type) VALUES (?, ?, ?)", (user_id, amount, trans_type))
    connection.commit()
    connection.close()

# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')  # Ensure 'index.html' exists in the templates folder

# Route for admin to register an agent
@app.route('/admin/register_agent', methods=['GET', 'POST'])
def register_agent():
    if 'user_id' in session:
        is_admin, is_master_agent, is_super_agent, is_user_agent = get_user_roles(session['user_id'])
        if is_master_agent:  # Only Master Agents can create Super Agents
            if request.method == 'POST':
                name = request.form['name']
                email = request.form['email']
                password = request.form['password']
                hashed_password = hash_password(password)
                
                connection = sqlite3.connect(DB_PATH)
                cursor = connection.cursor()
                cursor.execute("INSERT INTO users (username, email, password, is_admin, is_super_agent) VALUES (?, ?, ?, ?, ?)", 
                               (name, email, hashed_password, 0, 1))  # Super Agent created by Master Agent
                connection.commit()
                connection.close()
                flash("Super Agent registered successfully", "success")
                return redirect(url_for('admin_requests'))
            
            return render_template('register_agent.html')
        else:
            flash("You are not authorized to create agents.", "error")
            return redirect(url_for('index'))
    return redirect(url_for('signin'))

# Route to log out
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
