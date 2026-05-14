from flask import Flask, request, redirect, url_for, render_template, flash, session
from flask_hashing import Hashing
import MySQLdb
import os
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Use a secure key in production

# Initialize the hasher
hashing = Hashing(app)

# Database connection details
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Password'
DB_NAME = 'my_db'

# Connect to the database
db = MySQLdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
cursor = db.cursor()

def generate_salt():
    """Generate a random salt."""
    return base64.b64encode(os.urandom(16)).decode('utf-8')

def generate_hashed_password(password, salt):
    """Generate a hashed password using the provided salt."""
    return hashing.hash_value(password + salt, salt=salt)

def verify_password(stored_password_hash, provided_password, salt):
    """Verify a provided password against the stored hash."""
    return hashing.check_value(stored_password_hash, provided_password + salt)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and verify_password(user[2], password, user[3]):  # Assuming password_hash is the 3rd field and salt is the 4th field
            session['user_id'] = user[0]  # Assuming user_id is the 1st field
            session['username'] = user[1]  # Assuming username is the 2nd field
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    salt = generate_salt()
    print(salt)
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birth_date = request.form['birth_date']
        location = request.form['location']
        role = 'member'
        status ='active'

        salt = generate_salt()
        hashed_password = generate_hashed_password(password, salt)

        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, first_name, last_name, birth_date, location, role, status, salt)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (username, hashed_password, email, first_name, last_name, birth_date, location, role, status, salt))
            db.commit()
            flash('Registration successful. You can now log in.')
            return redirect(url_for('login'))
        except MySQLdb.Error as e:
            db.rollback()
            flash(f'Error: {e}')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return f'Hello, {session["username"]}'

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
