from flask import Flask, render_template, request, redirect, url_for, session,flash
from flask_mysqldb import MySQL
from flask_hashing import Hashing
import MySQLdb.cursors
from werkzeug.utils import secure_filename
import re, os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'Password@892'
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('m_home'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
         
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user and verify_password(user[2],password,salt): 
            session['user_id'] = user[0]  # Assuming user_id is the 1st field # Assuming username is the 2nd field
            session['role']= user[9]
            return redirect(url_for('m_home'))   
        else:
            flash('Invalid email or password')

    return render_template('auth/login.html',title="Login")


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
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
            ''', (username, hashed_password, email, first_name, last_name, birth_date, location,profile, role, status))
            db.commit()
            
            flash('Registration successful. You can now log in.')
            return redirect(url_for('login'))
        except MySQLdb.Error as e:
            db.rollback()
            flash(f'Error: {e}')

    return render_template('auth/registration.html')

@app.route('/')
def home():
    if 'user_id' in session:
        return "Yeah! You are logged in!!"
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
   session.pop('user_id', None)
   session.pop('role',None)
   flash("You logged out successfully!!")
   return redirect(url_for('login'))


@app.route('/a_user')
def a_user():
    if session['role']=='admin':
        cursor.execute('SELECT * FROM users' )
        db.commit()
        users = cursor.fetchall()
        print(users)
        return render_template('admin/user.html',users=users)


@app.route('/m_home')
def m_home():
    if session['role']=='member' or session['role']=='moderator':
        return render_template('member/home.html')
    if session['role']=='admin':
        return render_template('admin/home.html')



@app.route('/m_profile')
def m_profile():
    user_id = session['user_id']
    if not user_id:
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
    # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT username, email, first_name, last_name, birth_date, location, profile_image, role, status FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    print(user)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    if session['role']=='member'or session['role']=='modrator':
        return render_template('member/profile.html', user=user)
    if session['role']=='admin':
        return render_template('admin/profile.html',user=user)

@app.route('/delete_reply/<int:reply_id>')
def delete_reply(reply_id):
    try:
        query = "DELETE FROM replies WHERE reply_id = %s"
        cursor.execute(query, (reply_id,))
        db.commit()
        flash('Reply deleted successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash('An error occurred while deleting the reply: {}'.format(str(e)), 'danger')
    return redirect(url_for('m_chat'))


@app.route('/delete_message/<int:message_id>')
def delete_message(message_id):
    try:
        query = "DELETE FROM messages WHERE message_id = %s"
        cursor.execute(query, (message_id,))
        db.commit()
        flash('Message deleted successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash('An error occurred while deleting the message: {}'.format(str(e)), 'danger')
    return redirect(url_for('m_chat'))

@app.route('/edit_message', methods=['POST'])
def edit_message():
    try:
        message_id = request.form['message_id']
        title = request.form['title']
        content = request.form['content']
        
        query = """
        UPDATE messages
        SET title = %s, content = %s, created_at = NOW()
        WHERE message_id = %s
        """
        cursor.execute(query, (title, content, message_id))
        db.commit()
        
        flash('Message updated successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash('An error occurred while updating the message: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('m_chat'))


@app.route('/edit_reply', methods=['POST'])
def edit_reply():
    try:
        reply_id = request.form['reply_id']
        content = request.form['content']
        
        query = """
        UPDATE replies
        SET content = %s, created_at = NOW()
        WHERE reply_id = %s
        """
        cursor.execute(query, (content, reply_id))
        db.commit()
        
        flash('Reply updated successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash('An error occurred while updating the reply: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('m_chat'))


@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'user_id' in session:
        user_id = session['user_id']
        username = request.form['editedName']
        email=request.form['editedEmail']
        first_name = request.form['editedfirstname']
        last_name = request.form['editedlastname']
        birth_date = request.form['editedDob']
        location = request.form['editedlocation']
        cursor.execute('''UPDATE users 
                          SET username = %s,email=%s, first_name = %s, last_name = %s, birth_date = %s, location = %s 
                          WHERE user_id = %s''', 
                       (username, email,first_name, last_name, birth_date, location, user_id))
        db.commit()
        print("10")
        flash('Profile updated successfully', 'success')
        return redirect(url_for('m_profile'))
    return redirect(url_for('login'))

@app.route('/chnage_password', methods=['POST'])
def chnage_password():
    if request.method=="POST":
        if 'user_id' in session:
            user_id = session['user_id']
            old_password = request.form['oldPassword']
            new_password = request.form['editedPassword']
            # return redirect(url_for('m_profile'))

            cursor.execute('SELECT password_hash FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()
            print(user)
            if user:
                stored_password_hash = user[0]
                salt = 'pqrs' 
                print(salt) # Using username as salt
                if verify_password(stored_password_hash, old_password, salt):
                    print(user[0])
                    new_password_hash = generate_hashed_password(new_password, salt)
                    cursor.execute('UPDATE users SET password_hash = %s WHERE user_id = %s', (new_password_hash, user_id))
                    db.commit()
                    print("yeshh password upadted")
                    flash('Password changed successfully', 'success')                    
                return redirect(url_for('m_profile'))
            else:
                flash('Old password is incorrect', 'danger')
        else:
            flash('User not found', 'danger')
        return redirect(url_for('m_profile'))
    return redirect(url_for('login'))

     

@app.route('/post_message', methods=['POST'])
def post_message():
    print('hello')
    title = request.form['title']
    content = request.form['content']
    user_id = session['user_id']  # Assuming you have user_id stored in session
    if title and content:
        try:
            cursor.execute('INSERT INTO messages (user_id, title, content) VALUES (%s, %s, %s)', (user_id, title, content))
            db.commit()
            # db.engine.execute(query, (user_id, title, content))
            flash('Message posted successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        flash('Title and content are required.', 'danger')

    return redirect(url_for('m_chat'))

@app.route('/post_reply', methods=['POST'])
def post_reply():
    content = request.form['content']
    message_id = request.form['message_id']
    user_id = session['user_id']  # Assuming you have user_id stored in session

    if content:
        try:
            cursor.execute("INSERT INTO replies (message_id, user_id, content) VALUES (%s, %s, %s)", (message_id, user_id, content))
            db.commit()
            flash('Reply posted successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            db.connection.rollback()
    else:
        flash('Reply content is required.', 'danger')

    return redirect(url_for('m_chat'))


@app.route('/m_chat')
def m_chat():
    user_id = session.get('user_id')
    cursor.execute("""
    SELECT m.message_id, m.user_id, m.title, m.content, m.created_at, u.username,u.profile_image
    FROM messages m
    JOIN users u ON m.user_id = u.user_id
    ORDER BY m.created_at DESC
    """)
    messages = cursor.fetchall()
    db.commit()
    cursor.execute("""
    SELECT r.reply_id, r.message_id, r.user_id, r.content, r.created_at, u.username,u.profile_image
    FROM replies r
    JOIN users u ON r.user_id = u.user_id
    ORDER BY r.created_at ASC
    """)
    replies =cursor.fetchall()
    db.commit()
    replies_dict = {}
    for reply in replies:
        message_id = reply[1]  # Assuming message_id is the second column in replies table
        if message_id not in replies_dict:
            replies_dict[message_id] = []
            replies_dict[message_id].append(reply)
    if session['role']=='member':
        return render_template('member/chat.html', messages=messages, replies_dict=replies_dict,current_user_id=user_id)
    if session['role']=='moderator':
        return render_template('moderator/chat.html', messages=messages, replies_dict=replies_dict,current_user_id=user_id)
    if session['role']=='admin':
        return render_template('admin/chat.html', messages=messages, replies_dict=replies_dict,current_user_id=user_id)


@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if session['role']=='admin':
        if request.method == 'POST':
            user_id = request.form['user_id']
            role = request.form['role']
            status = request.form['status']
            query = "UPDATE users SET role = %s, status = %s WHERE user_id = %s"
            cursor.execute(query, (role, status, user_id))
            db.commit()
            return redirect(url_for('a_user'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/remove_image', methods=['POST'])
def remove_image():
    user_id = session.get('user_id')
    if not user_id:
        flash("You need to log in first", "error")
        return redirect(url_for('login'))
        # Fetch the user from the database
    user =session['user_id']
    profile_image = 'profile.png'
    cursor.execute("UPDATE users SET profile_image = %s WHERE user_id = %s", (profile_image, user))
    db.commit()
    flash("Profile photo removed successfully", "success")
    return redirect(url_for('m_profile'))
    
@app.route('/edit_photo', methods=['POST'])
def edit_photo():
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(url_for('m_profile'))
    
    file = request.files['photo']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('m_profile'))
    
    if file and allowed_file(file.filename):
        user_id=session['user_id']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cursor.execute("UPDATE users SET profile_image = %s WHERE user_id = %s", (filename, user_id))
        db.commit()
        flash('Profile photo updated successfully')
        return redirect(url_for('m_profile'))
       

if __name__ == '__main__':
    app.run(debug=True)


