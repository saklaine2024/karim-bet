from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to something unique

DB_PATH = "db/system.db"

# Helper function to check if the user is an admin
def is_admin(user_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    return user[0] == 1  # Assuming is_admin is a field in users table (1 = admin, 0 = normal user)

# Helper function to get balance (used for withdrawal)
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
        hashed_password = hash_password(password)

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
                       (username, hashed_password, 0))  # 0 is normal user, 1 would be for admin
        connection.commit()
        connection.close()

        flash("User created successfully!", "success")
        return redirect(url_for('signin'))
    return render_template('signup.html')

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
            session['user_id'] = user[0]  # Store user ID in session
            flash("Signed in successfully!", "success")
            return redirect(url_for('banking'))  # Redirect to banking page after successful login
        else:
            flash("Invalid username or password", "error")
    return render_template('signin.html')

# Route for banking page
@app.route('/banking')
def banking():
    if 'user_id' not in session:
        return redirect(url_for('signin'))  # Redirect to signin if not logged in

    user_id = session['user_id']
    balance = get_balance(user_id)
    return render_template('banking.html', balance=balance)

# Route to display pending requests (Admin view)
@app.route('/admin/requests')
def admin_requests():
    if 'user_id' in session and is_admin(session['user_id']):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM banking_requests WHERE status = 'pending'")
        requests = cursor.fetchall()
        connection.close()
        return render_template('admin_requests.html', requests=requests)
    else:
        return redirect(url_for('index'))

# Route to approve requests (Admin action)
@app.route('/admin/approve_request/<int:request_id>')
def approve_request(request_id):
    if 'user_id' in session and is_admin(session['user_id']):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM banking_requests WHERE id = ?", (request_id,))
        request = cursor.fetchone()

        if request:
            user_id = request[1]
            amount = request[3]
            request_type = request[4]

            if request_type == 'deposit':
                record_transaction(user_id, amount, 'deposit')  # Add to balance
            elif request_type == 'withdrawal':
                if get_balance(user_id) >= amount:
                    record_transaction(user_id, -amount, 'withdrawal')  # Deduct from balance
                else:
                    flash("Insufficient funds for withdrawal request.", "error")
                    return redirect(url_for('admin_requests'))

            cursor.execute("UPDATE banking_requests SET status = ?, reason = ? WHERE id = ?",
                           ('approved', '', request_id))
            connection.commit()

        connection.close()
        flash("Request approved successfully!", "success")
        return redirect(url_for('admin_requests'))

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
    return render_template('index.html')  # Ensure 'index.html' exists in the 'templates' folder

# Route for agent registration (Admin action)
@app.route('/admin/register_agent', methods=['GET', 'POST'])
def register_agent():
    if 'user_id' in session and is_admin(session['user_id']):
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            hashed_password = hash_password(password)
            
            # Insert agent into database
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO users (username, email, password, is_admin) VALUES (?, ?, ?, ?)", 
                           (name, email, hashed_password, 1))  # 1 for admin role (agent)
            connection.commit()
            connection.close()
            flash("Agent registered successfully", "success")
            return redirect(url_for('admin_requests'))
        
        return render_template('register_agent.html')
    else:
        return redirect(url_for('index'))

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user from session
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))  # Redirect to homepage after logout

if __name__ == '__main__':
    app.run(debug=True)
