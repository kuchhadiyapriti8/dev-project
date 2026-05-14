from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_mysqldb import MySQL
from flask_hashing import Hashing
import MySQLdb.cursors
import re
from app import app

app = Flask(__name__)

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Password'
DB_NAME = 'my_db'
# Intialize MySQL
mysql = MySQL(app)
hashing = Hashing(app)
app.secret_key = '1a2b3c4d5e6d7g8h9i10'

db = MySQLdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
cursor = db.cursor()
def generate_hashed_password(password, salt):
    """Generate a hashed password using the provided salt."""
    return hashing.hash_value(password, salt=salt)

def verify_password(stored_password_hash, provided_password, salt):
    """Verify a provided password against the stored hash."""
    return hashing.check_value(stored_password_hash, provided_password,salt)

salt='pqrs'

# http://localhost:5000/login/ - this will be the login page, we need to use both GET and POST requests
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    # Output message if something goes wrong...
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST':
        print("9")
        username = request.form['username']
        password = request.form['password']
         
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        print(user[2])
        print(password)
        print("10")
        if user and verify_password(user[2],password,salt): 
            print("11") # Assuming password_hash is the 3rd field and salt is the 4th field
            session['user_id'] = user[0]  # Assuming user_id is the 1st field
            session['username'] = user[1]  # Assuming username is the 2nd field
            session['role']= user[7]

            if session['role']=='admin':
                 return redirect(url_for('admin/home'))

            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')

    return render_template('login.html')


# http://localhost:5000/pythonlogin/register 
# This will be the registration page, we need to use both GET and POST requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        first_name = request.form['firstName']
        last_name = request.form['lastName']
        birth_date = request.form['birthDate']
        location = request.form['location']
        profile = 'profile.png'
        role = 'member'
        status = 'active'

       
        # Check if the username already exists
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Username already taken. Please choose a different username.')
            return render_template('registration.html')
        
        hashed_password = generate_hashed_password(password, salt)
        print(hashed_password)
        try:
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, first_name, last_name, birth_date, location,profile_image, role, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (username, hashed_password, email, first_name, last_name, birth_date, location, role, status))
            db.commit()
            
            flash('Registration successful. You can now log in.')
            return redirect(url_for('login'))
        except MySQLdb.Error as e:
            db.rollback()
            flash(f'Error: {e}')

    return render_template('registration.html')


# http://localhost:5000/pythinlogin/home 
# This will be the home page, only accessible for loggedin users

@app.route('/')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        return "yehh you are loged in!!"
        # User is loggedin show them the home page
        # return render_template('home/home.html', username=session['username'],title="Home")
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))    


# @app.route('/profile')
# def profile():
#     # Check if user is loggedin
#     if 'loggedin' in session:
#         # User is loggedin show them the home page
#         return render_template('auth/profile.html', username=session['username'],title="Profile")
#     # User is not loggedin redirect to login page
#     return redirect(url_for('login'))  

