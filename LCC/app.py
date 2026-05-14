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
DB_NAME = 'issue_tracker'

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



@app.route('/')
def home():
        return render_template('auth/home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        if session['status']=="active":
            return redirect(url_for('v_home'))
        else:
            print("here")
            flash("you are not allow to enter please contact admin")
    if request.method == 'POST':
        print(1)
        username = request.form['username']
        password = request.form['password']
         
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user and verify_password(user[2],password,salt): 
            session['user_id'] = user[0]  # Assuming user_id is the 1st field # Assuming username is the 2nd field
            session['role']= user[8]
            session['status']=user[9]
            return redirect(url_for('v_home'))   
        else:
            print("this is ")
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
        location = request.form['location']
        profile = 'profile.png'
        role = 'visitor'
        status = 'active'

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash('Username already taken. Please choose a different username.')
            return render_template('auth/registration.html')
        
        hashed_password = generate_hashed_password(password, salt)
        print(hashed_password)
        try:
            print("1")
            print("yaha to  aaa rha")
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, first_name, last_name,location,profile_image, role, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
            ''', (username, hashed_password, email, first_name, last_name,location,profile, role, status))           
            db.commit()
            flash('Registration successful. You can now log in.')
            return redirect(url_for('login'))
        except MySQLdb.Error as e:
            db.rollback()
            flash(f'Error: {e}')
    return render_template('auth/registration.html')


@app.route('/v_home')
def v_home():
    if session['role']=='visitor' or session['role']=='helper':
        return render_template('visitor/home.html')
    if session['role']=='admin':
        return render_template('admin/home.html')
    
@app.route('/v_profile')
def v_profile():
    user_id = session['user_id']
    if not user_id:
        flash('You must be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
    # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT username, email, first_name, last_name, location, profile_image, role, status FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    print(user)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    if session['role']=='visitor'or session['role']=='helper':
        return render_template('visitor/profile.html', user=user)
    if session['role']=='admin':
        return render_template('admin/profile.html',user=user)
    
@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    if 'user_id' in session:
        user_id = session['user_id']
        username = request.form['editedName']
        email=request.form['editedEmail']
        first_name = request.form['editedfirstname']
        last_name = request.form['editedlastname']
        location = request.form['editedlocation']
        cursor.execute('''UPDATE users 
                          SET username = %s,email=%s, first_name = %s, last_name = %s, location = %s 
                          WHERE user_id = %s''', 
                       (username, email,first_name, last_name, location, user_id))
        db.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('v_profile'))
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
            if user:
                stored_password_hash = user[0]
                salt = 'pqrs' 
                if verify_password(stored_password_hash, old_password, salt):
                    new_password_hash = generate_hashed_password(new_password, salt)
                    cursor.execute('UPDATE users SET password_hash = %s WHERE user_id = %s', (new_password_hash, user_id))
                    db.commit()
                    print("yeshh password upadted")
                    flash('Password changed successfully', 'success')                    
                    return redirect(url_for('v_profile'))
                else:
                    print("password incorrect")
                    flash('Old password is incorrect', 'danger')
                    return redirect(url_for('v_profile'))
            else:
                flash('User not found', 'danger')
            return redirect(url_for('v_profile'))
    return redirect(url_for('login'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/edit_photo', methods=['POST'])
def edit_photo():
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(url_for('v_profile'))
    
    file = request.files['photo']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('v_profile'))
    
    if file and allowed_file(file.filename):
        try:
            user_id = session['user_id']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            cursor.execute("UPDATE users SET profile_image = %s WHERE user_id = %s", (filename, user_id))
            db.commit()
            flash('Profile photo updated successfully')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
        return redirect(url_for('v_profile'))

    # Fallback for unexpected situations
    flash('Invalid file type or unexpected error')
    return redirect(url_for('v_profile'))



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
    return redirect(url_for('v_profile'))


@app.route('/issues/active')
def active_issues():
    user_id = session.get('user_id')
    print(user_id)
    cursor.execute("""
    SELECT m.issue_id, m.user_id, m.summary, m.status, m.description, u.username, u.profile_image
    FROM issues m
    JOIN users u ON m.user_id = u.user_id
    WHERE m.status IN ('new', 'open', 'stalled')
    ORDER BY m.created_at DESC
    """)
    active_issues = cursor.fetchall()

    cursor.execute("""
    SELECT r.comment_id, r.issue_id, r.user_id, r.content, r.created_at, u.username, u.profile_image
    FROM comments r
    JOIN users u ON r.user_id = u.user_id
    ORDER BY r.created_at ASC
    """)
    replies = cursor.fetchall()

    replies_dict = {}
    for reply in replies:
        message_id = reply[1]
        if message_id not in replies_dict:
            replies_dict[message_id] = []
        replies_dict[message_id].append(reply)

    if session['role'] == 'visitor':
        return render_template('visitor/chat.html', issues=active_issues, comments=replies_dict, current_user_id=user_id)

    if session['role'] == 'admin' or session['role'] == 'helper' :
        return render_template('admin/chat.html', issues=active_issues, comments=replies_dict, current_user_id=user_id)

@app.route('/issues/resolved')
def resolved_issues():
    user_id = session.get('user_id')
    cursor.execute("""
    SELECT m.issue_id, m.user_id, m.summary, m.status, m.description, u.username, u.profile_image
    FROM issues m
    JOIN users u ON m.user_id = u.user_id
    WHERE m.status = 'resolved'
    ORDER BY m.created_at DESC
    """)
    resolved_issues = cursor.fetchall()

    cursor.execute("""
    SELECT r.comment_id, r.issue_id, r.user_id, r.content, r.created_at, u.username, u.profile_image
    FROM comments r
    JOIN users u ON r.user_id = u.user_id
    ORDER BY r.created_at ASC
    """)
    replies = cursor.fetchall()

    replies_dict = {}
    for reply in replies:
        message_id = reply[1]
        if message_id not in replies_dict:
            replies_dict[message_id] = []
        replies_dict[message_id].append(reply)

    if session['role'] == 'visitor':
        return render_template('visitor/resolved_issues.html', issues=resolved_issues, comments=replies_dict, current_user_id=user_id)
    if session['role'] == 'helper':
        return render_template('helper/resolved_issues.html', issues=resolved_issues, comments=replies_dict, current_user_id=user_id)
    if session['role'] == 'admin':
        return render_template('admin/resolved_issues.html', issues=resolved_issues, comments=replies_dict, current_user_id=user_id)

@app.route('/post_message', methods=['POST'])
def post_message():
    print('hello')
    title = request.form['title']
    content = request.form['content']
    user_id = session['user_id'] 
    status="new" # Assuming you have user_id stored in session
    if title and content:
        try:
            cursor.execute('INSERT INTO issues(user_id, summary, description ,status) VALUES (%s, %s, %s,%s)', (user_id, title, content,status))
            db.commit()
            # db.engine.execute(query, (user_id, title, content))
            flash('Message posted successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        flash('Title and content are required.', 'danger')

    return redirect(url_for('active_issues'))


@app.route('/add_comment', methods=['POST'])
def add_comment():
    content = request.form['content']
    issue_id = request.form['issue_id']
    user_id = session['user_id']  # Assuming you have user_id stored in session
    if content:
        try:
            cursor.execute("INSERT INTO comments(issue_id, user_id, content) VALUES (%s, %s, %s)", (issue_id, user_id, content))
            db.commit()
            flash('Reply posted successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            db.connection.rollback()
    else:
        flash('Reply content is required.', 'danger')

    return redirect(url_for('active_issues'))

@app.route('/edit_issue_status', methods=['POST'])
def edit_issue_status():
    try:
        issue_id = request.form['issue_id']
        status=request.form['status']
        
        query = """
        UPDATE issues
        SET status=%s
        WHERE issue_id = %s
        """
        cursor.execute(query, ( status, issue_id))
        db.commit()
        
        flash('Message updated successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash('An error occurred while updating the message: {}'.format(str(e)), 'danger')
    
    return redirect(url_for('active_issues'))




@app.route('/logout')
def logout():
   session.pop('user_id', None)
   session.pop('role',None)
   session.pop('status',None)
   flash("You logged out successfully!!")
   return redirect(url_for('login'))

@app.route('/a_user')
def a_user():
    if session['role']=='admin':
        cursor.execute('SELECT * FROM users' )
        db.commit()
        users = cursor.fetchall()
        return render_template('admin/user.html',users=users)

@app.route('/manage_users', methods=['GET', 'POST'])
def manage_users():
    if session['role']=='admin':
        if request.method == 'POST':
            user_id = request.form['user_id']
            role = request.form['role']
            status = request.form['status']
            print(role)
            print(status)
            query = "UPDATE users SET role = %s, status = %s WHERE user_id = %s"
            cursor.execute(query, (role, status, user_id))
            db.commit()
            return redirect(url_for('a_user'))
        
if __name__ == '__main__':
    app.run(debug=True)






