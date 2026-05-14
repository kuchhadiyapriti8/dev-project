from yogoapp import app
from yogoapp import db
from flask import redirect, render_template, request, session, url_for, flash, Blueprint
from flask_bcrypt import Bcrypt
import re
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from flask import send_file

flask_bcrypt = Bcrypt(app)

# Default role
DEFAULT_USER_ROLE = 'traveller'
DEFAULT_USER_STATUS = 'active'

def user_home_url():
    """Generates a URL to the homepage for the currently logged-in user.

    If the user is not logged in, or the role stored in their session cookie is
    invalid, this returns the URL for the login page instead."""
    role = session.get('role', None)

    if role=='traveller':
        home_endpoint='traveller_home'
    elif role=='editor' or role =="support_tech":
        home_endpoint='editor_home'
    elif role=='admin':
        home_endpoint='admin_home'
    else:
        home_endpoint = 'login'

    return url_for(home_endpoint)

def is_staff():
    if 'loggedin' in session:
        with db.get_cursor() as cursor:
            cursor.execute('SELECT role FROM users WHERE user_id = %s', (session['user_id'],))
            user = cursor.fetchone()
            return user and user['role'] in ['admin', 'editor', 'support_tech']
    return False

def image_exists(image_path):
    try:
        return os.path.exists(os.path.join(app.static_folder, image_path))
    except Exception:
        return False

app.jinja_env.globals.update(image_exists=image_exists)

@app.route('/')
def root():
    """Root endpoint (/)
    Renders the homepage for all users.
    """
    # get published journals from database
    with db.get_cursor() as cursor:
        cursor.execute('''
            SELECT j.*, u.username FROM journals j
            JOIN users u ON j.user_id = u.user_id
            WHERE j.j_published = 'yes'
            ORDER BY j.j_startdate DESC
        ''')
        published_journals = cursor.fetchall()
        
        for journal in published_journals:
            cursor.execute('SELECT * FROM events WHERE journal_id = %s;', (journal['journal_id'],))
            events = cursor.fetchall()
            journal['events'] = events

            
    return render_template('homepage.html', published_journals=published_journals)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' in session:
        return redirect(user_home_url())

    error_message = None
    username_invalid = False
    password_invalid = False
    username = ''

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username and password:
            with db.get_cursor() as cursor:
                cursor.execute('SELECT user_id, username, password_hash, user_status, subscription_status, role FROM users WHERE username = %s;', (username,))
                account = cursor.fetchone()

                if not account:
                    error_message = "The username is not registered. Please sign up first."
                    username_invalid = True
                    return render_template('login.html', error_message=error_message, username_invalid=username_invalid)
                if isinstance(account['password_hash'], bytearray):
                    account['password_hash'] = bytes(account['password_hash'])

                if not flask_bcrypt.check_password_hash(account['password_hash'], password):
                    error_message = "Wrong password, please try again."
                    password_invalid = True
                    return render_template('login.html', error_message=error_message, password_invalid=password_invalid)
                if account['user_status']== 'ban_all':
                    error_message="you can't access that account as your account is banned. "
                    return render_template('login.html', error_message=error_message)

                session.update({
                        'loggedin': True,
                        'user_id': account['user_id'],
                        'username': account['username'],
                        'role': account['role'],
                        'subscription_status':account['subscription_status'],
                        'status':account['user_status']
                    })
                print("Sessionn after login:", session)
                return redirect(user_home_url())
        else:
            error_message = "Enter your username and password."
            username_invalid = True
            password_invalid = True

    return render_template('login.html', username=username, error_message=error_message, username_invalid=username_invalid, password_invalid=password_invalid)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'loggedin' in session:
        return redirect(user_home_url())

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        location = request.form['location'].strip()

        errors = {}

        if not re.match(r'^[A-Za-z0-9]+$', username):
            errors['username'] = 'Username can only contain letters and numbers.'
        if len(email) > 320 or not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            errors['email'] = 'Invalid email address.'
        if password != confirm_password:
            errors['password'] = 'Passwords do not match.'
        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            errors['password_strength'] = 'Password must be at least 8 characters long and include letters and numbers.'

        with db.get_cursor() as cursor:
            cursor.execute('SELECT user_id FROM users WHERE username = %s OR email = %s;', (username, email))
            if cursor.fetchone():
                errors['exists'] = 'Username or email already in use.'

        if errors:
            return render_template('signup.html', errors=errors, username=username, email=email, first_name=first_name, last_name=last_name, location=location)

        password_hash = flask_bcrypt.generate_password_hash(password)
        with db.get_cursor() as cursor:
            cursor.execute('''INSERT INTO users (username, password_hash, email, first_name, last_name, location, role, user_status)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s);''',
                           (username, password_hash, email, first_name, last_name, location, DEFAULT_USER_ROLE, DEFAULT_USER_STATUS))

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/support/toggle_ban_user', methods=['POST'])
def toggle_ban_user():
    if 'role' not in session or session['role'] != 'support_tech':
        flash('Access denied.', 'danger')
        return redirect(url_for('support_view_users'))

    user_id = request.form.get('user_id')
    current_status = request.form.get('current_status')
    reason = request.form.get('reason', 'unban')  # Will be empty if unbanning

    try:
        with db.get_cursor() as cursor:
            if current_status == 'active':
                # Ban user with reason; here I choose ban_share as the ban status,
                # but you can change this logic if you want to toggle between ban_share and ban_all
                new_status = 'ban_share'
                cursor.execute('''
                    UPDATE users
                    SET user_status = %s
                    WHERE user_id = %s
                ''', (new_status, user_id))

                cursor.execute('''
                    INSERT INTO ban_logs (user_id, action, reason, ban_date)
                    VALUES (%s, %s, %s, NOW())
                ''', (user_id, 'banned', reason))

            else:
                # Unban user
                new_status = 'active'
                cursor.execute('''
                    UPDATE users
                    SET user_status = %s
                    WHERE user_id = %s
                ''', (new_status, user_id))

                cursor.execute('''
                    INSERT INTO ban_logs (user_id, action,ban_date)
                    VALUES (%s, %s, NOW())
                ''', (user_id, 'unbanned'))

        flash(f'User has been {new_status}.', 'success')

    except Exception as e:
        flash(f'Error toggling user status: {str(e)}', 'danger')
        app.logger.error(f'Ban toggle error: {str(e)}', exc_info=True)

    return redirect(url_for('support_view_users'))




@app.route('/profile')
def profile():
    if 'loggedin' not in session:
         return redirect(url_for('login'))

    with db.get_cursor() as cursor:
        # users all info 
        cursor.execute('SELECT * FROM users WHERE user_id = %s;',
                       (session['user_id'],))
        profile = cursor.fetchone()
        
        # subscription info, for showing up these info in profile pages
        with db.get_cursor() as sub_cursor:
                sub_cursor.execute('''
                    SELECT us.*, sp.plan_name as plan_name
                    FROM user_subscriptions us
                    JOIN subscription_plans sp ON us.plan_name = sp.plan_name
                    WHERE us.user_id = %s 
                    AND us.end_date >= CURRENT_DATE
                    ORDER BY us.end_date DESC
                    LIMIT 1
                ''', (session['user_id'],))
                subscription = sub_cursor.fetchone()

    return render_template('profile.html', 
                         profile=profile,
                         subscription=subscription)

@app.route('/upload_image',methods=['POST'])
def upload_image():
    if 'photo' not in request.files:
        flash('No file part')
        return redirect(url_for('v_profile'))

    file = request.files['photo']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        try:
            user_id = session['user_id']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with db.get_cursor() as cursor:
                cursor.execute("UPDATE users SET profile_image = %s WHERE user_id = %s", (filename, user_id))
                flash('Profile photo updated successfully')
        except Exception as e:
            flash(f'An error occurred: {str(e)}')
        return redirect(url_for('profile'))

    # Fallback for unexpected situations
    flash('Invalid file type ')
    return redirect(url_for('profile'))


@app.route('/remove_image',methods=['POST'])
def remove_image():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        # Fetch the user from the database
    user =session['user_id']
    profile_image = 'default.png'
    with db.get_cursor() as cursor:
        cursor.execute("UPDATE users SET profile_image = %s WHERE user_id = %s", (profile_image, user))
        flash("Profile photo removed successfully", "success")
        return redirect(url_for('profile'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' in session:
        user_id = session['user_id']
        username = request.form['username']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        location = request.form['location']

        with db.get_cursor() as cursor:
            # Check if the email already exists for another user
            cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (email, user_id))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email is already in use by another account.', 'danger')
                return redirect(url_for('profile'))

            # Update user details if email is unique
            cursor.execute('''
                UPDATE users
                SET username = %s, email = %s, first_name = %s, last_name = %s, location = %s
                WHERE user_id = %s
            ''', (username, email, first_name, last_name, location, user_id))

            flash('Profile updated successfully', 'success')
            return redirect(url_for('profile'))

    return redirect(url_for('login'))


@app.route('/change_password',methods=['POST'])
def change_password():
    if request.method=="POST":
        if 'user_id' in session:
            user_id = session['user_id']
            old_password = request.form['old_password']
            new_password = request.form['new_password']
            # return redirect(url_for('m_profile'))
            with db.get_cursor() as cursor:
                cursor.execute('SELECT password_hash FROM users WHERE user_id = %s', (user_id,))
                user = cursor.fetchone()
                if user:
                    stored_password_hash = user['password_hash']
                    print(stored_password_hash)
                    old_hash_password=flask_bcrypt.generate_password_hash(old_password)
                    test=flask_bcrypt.generate_password_hash('admin1pass')
                    print("test"+str(test))
                    print(old_password)
                    print(old_hash_password)
                    print(flask_bcrypt.check_password_hash(stored_password_hash, old_password))
                    if flask_bcrypt.check_password_hash(stored_password_hash, old_password):
                        new_password_hash = flask_bcrypt.generate_password_hash(new_password)
                        cursor.execute('UPDATE users SET password_hash = %s WHERE user_id = %s', (new_password_hash, user_id))
                        # db.commit()
                        print("yeshh password upadted")
                        flash('Password changed successfully', 'success')
                        return redirect(url_for('profile'))
                    else:
                        print("password incorrect")
                        flash('Old password is incorrect', 'danger')
                        return redirect(url_for('profile'))
                else:
                    flash('User not found', 'danger')
                    return redirect(url_for('profile'))
        return redirect(url_for('login'))


#change journey status to published
#no yet working 
@app.route('/publish_journal/<int:journal_id>', methods=['POST'])
def publish_journal(journal_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    with db.get_cursor() as cursor:
        cursor.execute("SELECT j_published FROM journals WHERE journal_id = %s AND user_id = %s", 
                      (journal_id, session['user_id']))
        journal = cursor.fetchone()
        
        if journal and journal['j_published'] == 'yes':
            cursor.execute("UPDATE journals SET j_published = 'no' WHERE journal_id = %s AND user_id = %s", 
                          (journal_id, session['user_id']))
            flash('Journal unpublished from homepage', 'success')
        else:
            cursor.execute("UPDATE journals SET j_published = 'yes' WHERE journal_id = %s AND user_id = %s", 
                          (journal_id, session['user_id']))
            flash('Journal published to homepage', 'success')
    
    return redirect(url_for('myjournal'))

@app.route('/myjournal')
def myjournal():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    my_journals = []
    my_journey_is_empty = True

    with db.get_cursor() as cursor:


        cursor.execute('SELECT journal_id, j_title, j_description, j_startdate, j_status, j_published FROM journals WHERE user_id = %s ORDER BY j_startdate DESC;', (user_id,))
        my_journals = cursor.fetchall()

        if my_journals:
            my_journey_is_empty = False
            for journal in my_journals:
                cursor.execute('SELECT * FROM events WHERE journal_id = %s ORDER BY e_startdatetime DESC;', (journal['journal_id'],))
                events = cursor.fetchall()
                for event in events:
                    if event['e_enddatetime'] and event['e_startdatetime']:
                        duration = round((event['e_enddatetime'] - event['e_startdatetime']).total_seconds() / 3600, 1)
                        event['duration'] = duration
                    else:
                        event['duration'] = 0
            journal['events'] = events

        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT DISTINCT e.e_location
                FROM events e
                JOIN journals j ON e.journal_id = j.journal_id
                WHERE j.user_id = %s
            ''', (user_id,))
            locations = cursor.fetchall()

    return render_template('myjournal.html', my_journals=my_journals, my_journey_is_empty=my_journey_is_empty, locations=locations)

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('status',None)
    return redirect(url_for('root'))
    #session.pop('last_name', None)
    #session.pop('first_name', None)
    #session.pop('location', None)


# get upload funtion, copy and modified it from flask offcial document https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/add_event/<int:journal_id>', methods=['POST'])
def add_event(journal_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        e_title = request.form['e_title']
        e_description = request.form['e_description']
        e_startdatetime = request.form['e_startdatetime']
        e_enddatetime = request.form['e_enddatetime'] or None
        e_location = request.form['e_location']
        e_cover = request.form['e_cover'] == 'true'

        with db.get_cursor() as cursor:
            cursor.execute('SELECT j_startdate FROM journals WHERE journal_id = %s', (journal_id,))
            journal = cursor.fetchone()
            journal_start = journal['j_startdate']

            if e_enddatetime:
                start_time = datetime.strptime(e_startdatetime, '%Y-%m-%dT%H:%M')
                end_time = datetime.strptime(e_enddatetime, '%Y-%m-%dT%H:%M')
                event_start_date = start_time.date()

                if end_time <= start_time or event_start_date < journal_start:
                    return redirect(url_for('myjournal', time_error=True, journal_id=journal_id))

        e_image = None
        if 'e_image' in request.files:
            file = request.files['e_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                e_image = 'uploads/' + filename
            elif file.filename != '' and not allowed_file(file.filename):
                flash('file type is not allowed')
                return redirect(url_for('myjournal'))

        if e_cover:
            with db.get_cursor() as cursor:
                cursor.execute('''UPDATE journals SET cover_image = %s WHERE journal_id = %s''', (e_image, journal_id))
        with db.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO events (e_title, e_description, e_startdatetime, e_enddatetime,
                                  e_location, e_image, journal_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (e_title, e_description, e_startdatetime, e_enddatetime,
                  e_location, e_image, journal_id))



    return redirect(url_for('myjournal'))


@app.route('/add_journal', methods=['POST'])
def add_journal():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        j_title = request.form['j_title']
        j_description = request.form['j_description']
        j_startdate = request.form['j_startdate']
        j_status = request.form['j_status']
        user_id = session['user_id']

        with db.get_cursor() as cursor:
            cursor.execute('''
                INSERT INTO journals (j_title, j_description, j_startdate, j_status, user_id)
                VALUES (%s, %s, %s, %s, %s)
            ''', (j_title, j_description, j_startdate, j_status, user_id))

    return redirect(url_for('myjournal'))

@app.route('/allpublicjournal', methods=['GET', 'POST'])
def allpublicjournal():
    if 'loggedin' not in session:
        return render_template('access_denied.html'), 403

    search_query = request.args.get('search', '')
    query_conditions = ''
    parameters = []

    if search_query:
        query_conditions = '''
            AND (j.j_title LIKE %s OR j.j_description LIKE %s)
        '''
        parameters.extend(['%' + search_query + '%', '%' + search_query + '%'])

    with db.get_cursor() as cursor:
        cursor.execute('''
            SELECT j.*, u.username
            FROM journals j
            JOIN users u ON j.user_id = u.user_id
            WHERE j.j_status = 'public'
            ''' + query_conditions + '''
            ORDER BY j.j_startdate DESC
        ''', parameters)

        journals = cursor.fetchall()
        my_journey_is_empty = True
        if journals:
            my_journey_is_empty = False
            for journal in journals:
                cursor.execute('SELECT * FROM events WHERE journal_id = %s;', (journal['journal_id'],))
                events = cursor.fetchall()
                for event in events:
                    if event['e_enddatetime'] and event['e_startdatetime']:
                        duration = round((event['e_enddatetime'] - event['e_startdatetime']).total_seconds() / 3600, 1)
                        event['duration'] = duration
                    else:
                        event['duration'] = 0
                journal['events'] = events

    return render_template('alljournaltraveller.html', journals=journals, my_journey_is_empty=my_journey_is_empty, search_query=search_query)


@app.route('/statuschange', methods=['POST'])
def status_change():
    if 'loggedin' not in session:
        return render_template('access_denied.html'), 403

    if request.method == 'POST':
        journal_id = request.form['journal_id']
        j_status = request.form['j_status']
        if(j_status == "public"):
            j_status = "private"
        else:
            j_status = "public"

        with db.get_cursor() as cursor:
            cursor.execute('''
                UPDATE journals SET j_status = %s
                WHERE journal_id = %s ''', (j_status, journal_id))

    return redirect(url_for('myjournal'))




#sprint2- editing or delete own journal
@app.route('/edit_myjournal/<int:journal_id>', methods=['GET', 'POST'])
def edit_myjournal(journal_id):
    # admin and editor has all same right to edit as premium user
    if session.get('role') in ['admin', 'editor']:
        subscription = {'is_premium': True, 'is_free_trial': False}
    else:
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT TRUE as is_premium
                FROM user_subscriptions
                WHERE user_id = %s AND end_date >= CURDATE()
                ORDER BY end_date DESC LIMIT 1
            ''', (session['user_id'],))
            subscription = cursor.fetchone()

    if 'loggedin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        j_title = request.form['j_title']
        j_description = request.form['j_description']
        j_startdate = request.form['j_startdate']

        with db.get_cursor() as cursor:
            cursor.execute('''
                UPDATE journals
                SET j_title = %s, j_description = %s, j_startdate = %s
                WHERE journal_id = %s AND user_id = %s
            ''', (j_title, j_description, j_startdate, journal_id, session['user_id']))
        return redirect(url_for('myjournal'))


    with db.get_cursor() as cursor:
        cursor.execute('''
            SELECT * FROM journals
            WHERE journal_id = %s AND user_id = %s
        ''', (journal_id, session['user_id']))
        journal = cursor.fetchone()

        if not journal:
            return redirect(url_for('myjournal'))

        cursor.execute('SELECT * FROM events WHERE journal_id = %s ORDER BY e_startdatetime DESC', (journal_id,))
        events = cursor.fetchall()

        cursor.execute('SELECT DISTINCT e_location FROM events ORDER BY e_location')
        locations = cursor.fetchall()

    return render_template('edit_journal.html', journal=journal, events=events, locations=locations,
                         subscription=subscription) 

@app.route('/delete_myjournal/<int:journal_id>', methods=['POST'])
def delete_myjournal(journal_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    with db.get_cursor() as cursor:
        cursor.execute('DELETE FROM events WHERE journal_id = %s', (journal_id,))
        cursor.execute('DELETE FROM journals WHERE journal_id = %s AND user_id = %s',
                      (journal_id, session['user_id']))

    return redirect(url_for('myjournal'))


#
#
@app.route('/edit_event/<int:event_id>', methods=['POST'])
def edit_event(event_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    # only admin editor and premium user can edit
    if session.get('role') in ['admin', 'editor']:
        subscription = {'is_premium': True, 'is_free_trial': False}
    else:
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT TRUE as is_premium
                FROM user_subscriptions
                WHERE user_id = %s AND end_date >= CURDATE()
                ORDER BY end_date DESC LIMIT 1
            ''', (session['user_id'],))
            subscription = cursor.fetchone()
        
        if not subscription:
            flash('You have no current subscription, please become a premium first. ', 'warning')
            return redirect(url_for('subscribe'))


    e_title = request.form['e_title']
    e_description = request.form['e_description']
    e_startdatetime = request.form['e_startdatetime']
    e_enddatetime = request.form['e_enddatetime'] or None
    e_location = request.form['e_location']

    # get current e_image, project 1 was vchar, in project 2, e_image changed to TEXT so can store multyiple images
    with db.get_cursor() as cursor:
        cursor.execute('SELECT e_image FROM events WHERE event_id = %s', (event_id,))
        current_images = cursor.fetchone()['e_image'] or ''
        image_list = current_images.split(',') if current_images else []

    # image upload
    if 'e_image' in request.files:
        file = request.files['e_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_list.append('uploads/' + filename)

    # image delete
    if 'remove_image' in request.form:
        try:
            index = int(request.form['remove_image'])
            if 0 <= index < len(image_list):
                try:
                    os.remove(os.path.join(app.static_folder, image_list[index]))
                except:
                    pass
                image_list.pop(index)
        except:
            pass

    # update event to datatabase 
    with db.get_cursor() as cursor:
        cursor.execute('''
            UPDATE events
            SET e_title = %s, e_description = %s,
                e_startdatetime = %s, e_enddatetime = %s,
                e_location = %s, e_image = %s
            WHERE event_id = %s
        ''', (e_title, e_description, e_startdatetime,
              e_enddatetime, e_location, 
              ','.join(image_list) if image_list else None,
              event_id))
    flash('Event updated successfully!', 'success')

    return redirect(request.referrer)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    with db.get_cursor() as cursor:
        cursor.execute('DELETE FROM events WHERE event_id = %s', (event_id,))

    return redirect(url_for('myjournal'))

@app.route('/edit_event_location/<int:event_id>', methods=['POST'])
def edit_event_location(event_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] not in ['editor', 'admin']:
        return render_template('access_denied.html'), 403

    new_location = request.form.get('e_location')

    if new_location:
        with db.get_cursor() as cursor:
            # Update the event location
            cursor.execute('''
                UPDATE events
                SET e_location = %s
                WHERE event_id = %s
            ''', (new_location, event_id))

            # Log the location change in the 'changes' table
            cursor.execute('''
                INSERT INTO changes (new_location, changed_date, changed_by, event_id)
                VALUES (%s, NOW(), %s, %s)
            ''', (new_location, session['user_id'], event_id))

            flash('Event location updated successfully!', 'success')

    return redirect(url_for('alljournal'))


@app.route('/premium')
def premium():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT us.*, sp.plan_name, sp.months, sp.price_incl_gst, sp.discount_percent
                FROM user_subscriptions us
                JOIN subscription_plans sp ON us.plan_name = sp.plan_name
                WHERE us.user_id = %s 
                AND us.end_date > CURDATE()
                ORDER BY us.end_date DESC 
                LIMIT 1
            ''', (session['user_id'],))
            active_subscription = cursor.fetchone()

            cursor.execute('''
                SELECT * FROM subscription_plans 
                WHERE is_admin_grant = 0
                ORDER BY months ASC
            ''')
            plans = cursor.fetchall()

            cursor.execute('''
                SELECT * FROM user_subscriptions 
                WHERE user_id = %s 
                AND plan_name = %s
            ''', (session['user_id'], 'trial'))
            existing_subscription = cursor.fetchone()

            cursor.fetchall()
            
            return render_template('premium.html', 
                                active_subscription=active_subscription,
                                plans=plans,existing_subscription=existing_subscription)

@app.route('/start_free_trial', methods=['GET', 'POST'])
def start_free_trial():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = %s', ('Free Trial',))
        trial_plan = cursor.fetchone()

        if request.method == 'POST':
            # Check if user already has an active subscription
            cursor.execute('''
                SELECT * FROM user_subscriptions 
                WHERE user_id = %s 
                AND plan_name = %s
            ''', (session['user_id'], 'Free Trial'))
            existing_subscription = cursor.fetchone()
            
            if existing_subscription:
                return render_template('premium.html', existing_subscription=existing_subscription)
            
            # Calculate dates
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=31)
            
            # Create new subscription
            cursor.execute('''
                INSERT INTO user_subscriptions 
                (user_id, plan_name, start_date, end_date)
                VALUES (%s, %s, %s, %s)
            ''', (session['user_id'], trial_plan['plan_name'], start_date, end_date))

            # create a payment record
            cursor.execute('''
                INSERT INTO payments 
                (subscription_id, amount_paid, payment_date)
                VALUES (%s, %s, %s)
            ''', (cursor.lastrowid, trial_plan['price_incl_gst'], datetime.now()))

            # Update user's subscription status
            cursor.execute('''
                UPDATE users 
                SET subscription_status = 'Premium', 
                    subscription_expiry = %s 
                WHERE user_id = %s
            ''', (end_date, session['user_id']))
            
            flash('Your free trial has started successfully!', 'success')
            return redirect(url_for('premium'))
        
        # For GET request, redirect to premium page
        return redirect(url_for('premium'))

@app.route('/payment/<plan_name>')
def payment(plan_name):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = %s', (plan_name,))
        plan = cursor.fetchone()
    return render_template('payment.html', plan=plan)

@app.route('/process_payment/<plan_name>', methods=['POST'])
def process_payment(plan_name):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    # get the country
    country = request.form.get('country', 'NZ')
    
    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = %s', (plan_name,))
        plan = cursor.fetchone()      
        # get current active subscription if any
        cursor.execute('''
            SELECT * FROM user_subscriptions 
            WHERE user_id = %s 
            AND end_date > CURDATE()
            ORDER BY end_date DESC
            LIMIT 1
        ''', (session['user_id'],))
        current_subscription = cursor.fetchone()
        
        # calculate dates
        start_date = datetime.now().date()
        if current_subscription:
            # if there's an active subscription, extend from its end date
            end_date = current_subscription['end_date']
            # add months to the end date
            if plan['months'] == 12:
                start_date = current_subscription['end_date']
                end_date = end_date.replace(year=end_date.year + 1)
                
            else:
                start_date = current_subscription['end_date']
                end_date = current_subscription['end_date'] + timedelta(days=31 * plan['months'])
        else:
            # if no active subscription, start from today
            if plan['months'] == 12:
                # for yearly plans, add one year
                end_date = start_date.replace(year=start_date.year + 1)
            else:
                # for monthly plans
                end_date = start_date + timedelta(days=31 * plan['months'])
        # gst should be charged based on country
        gst_charged = country == 'NZ'
        amount_paid = plan['price_incl_gst'] if gst_charged else plan['price_excl_gst']
        gst_amount = plan['price_incl_gst'] - plan['price_excl_gst'] if gst_charged else 0
        
        # create new subscription
        cursor.execute('''
            INSERT INTO user_subscriptions 
            (user_id, plan_name, start_date, end_date)
            VALUES (%s, %s, %s, %s)
        ''', (session['user_id'], plan['plan_name'], start_date, end_date))
        
        # get the subscription_id of the newly created subscription
        subscription_id = cursor.lastrowid
        
        # record the payment
        cursor.execute('''
            INSERT INTO payments 
            (subscription_id, card_last4, billing_country, amount_paid, payment_date)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
              subscription_id,
              request.form.get('card_number')[-4:],  # store last 4 digits of card
              country,
              amount_paid,
              datetime.now()))
        
        # update user's subscription status
        cursor.execute('''
            UPDATE users 
            SET subscription_status = 'Premium', 
                subscription_expiry = %s 
            WHERE user_id = %s
        ''', (end_date, session['user_id']))
        
        return render_template('payment_success.html',
                             plan=plan,
                             amount_paid=amount_paid,
                             gst_charged=gst_charged,
                             gst_amount=gst_amount,
                             end_date=end_date)

# @app.route('/subscribe/<plan_name>', methods=['POST'])
# def subscribe(plan_name):
#     if 'loggedin' not in session:
#         return redirect(url_for('login'))
#     return redirect(url_for('payment', plan_name=plan_name))

@app.route('/View_subscription')
def View_subscription():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    with db.get_cursor() as cursor:
        cursor.execute('''
            SELECT us.*,p.payment_date, sp.plan_name,sp.is_free_trial, sp.is_admin_grant, sp.months, p.amount_paid, p.card_last4, p.billing_country
            FROM user_subscriptions us
            INNER JOIN subscription_plans sp ON us.plan_name = sp.plan_name
            LEFT JOIN payments p ON us.subscription_id = p.subscription_id 
            WHERE us.user_id = %s 
            ORDER BY us.start_date DESC
        ''', (session['user_id'],))
        subscriptions = cursor.fetchall()
    
    return render_template('subscription_history.html', 
                         subscriptions=subscriptions,
                         now=datetime.now().date())

@app.route('/View_subscription/view_receipt',methods=['POST'])
def view_receipt():
    if request.method=="POST":
        sub_id = request.form.get("sub_id")
        plan_name = request.form.get("plan_name")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        pay_date = request.form.get("pay_date")
        amount_paid = request.form.get("amount_paid")
        card_last4 = request.form.get("card_last4")
        billing_country = request.form.get("billing_country")
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT p.amount_paid-sp.price_excl_gst as gst_paid
                FROM user_subscriptions us
                INNER JOIN subscription_plans sp ON us.plan_name = sp.plan_name
                INNER JOIN payments p ON us.subscription_id = p.subscription_id 
                WHERE us.user_id = %s and us.subscription_id=%s
            ''', (session['user_id'],sub_id))
            gst_paid = cursor.fetchone()
            cursor.execute('''select users.username from users where users.user_id = %s''',(session['user_id'],))
            username = cursor.fetchone()

    return render_template('receipt.html',gst_paid=gst_paid,
                           plan_name=plan_name,
                           start_date=start_date,
                           end_date=end_date,
                           pay_date=pay_date,
                           amount_paid=amount_paid,
                           card_last4=card_last4,billing_country=billing_country,username=username)


# @app.route('/download/<subscription_id>', methods=['POST'])
# def download_receipt():
#     if request.method=="POST":
#         sub_id = request.form.get("sub_id")
#         with db.get_cursor() as cursor:
#             cursor.execute('''
#                 SELECT us.*,p.payment_date, sp.plan_name, sp.months, p.amount_paid, p.card_last4, p.billing_country
#                 FROM user_subscriptions us
#                 INNER JOIN subscription_plans sp ON us.plan_name = sp.plan_name
#                 INNER JOIN payments p ON us.subscription_id = p.subscription_id 
#                 WHERE us.user_id = %s and subscription_id=%s
#             ''', (session['user_id'],sub_id))
#     return render_template('path/to/receipt.pdf', as_attachment=True)


@app.route('/yogopro')
def yogopro():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    # Use session subscription_status to check permission
    if session.get('subscription_status', '').lower() != 'premium':
        flash('You need a premium subscription to access YOGO premium features', 'warning')
        return redirect(url_for('premium'))

    with db.get_cursor() as cursor:
        cursor.execute('''
            SELECT DISTINCT j.journal_id, j.j_title, j.j_description, j.j_startdate, j.j_status, u.username
            FROM journals j
            JOIN users u ON j.user_id = u.user_id
            WHERE j.j_status = 'public'
            ORDER BY j.j_startdate DESC
        ''')
        journals = cursor.fetchall()
        my_journey_is_empty = not bool(journals)

        # Add duration into journals
        for journal in journals:
            cursor.execute('SELECT * FROM events WHERE journal_id = %s;', (journal['journal_id'],))
            events = cursor.fetchall()
            for event in events:
                if event['e_enddatetime'] and event['e_startdatetime']:
                    duration = round((event['e_enddatetime'] - event['e_startdatetime']).total_seconds() / 3600, 1)
                    event['duration'] = duration
                else:
                    event['duration'] = 0
            journal['events'] = events

    return render_template('yogopro.html', 
                         journals=journals, 
                         my_journey_is_empty=my_journey_is_empty)


@app.route('/changelog', methods=['POST'])
def changelog():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        journal_id = request.form['journal_id']
        with db.get_cursor() as cursor:
            cursor.execute("""SELECT c.change_id, u.username, c.new_location, c.changed_date, c.event_id, e.journal_id
                                FROM changes c JOIN users u ON c.changed_by = u.user_id
                                JOIN events e ON c.event_id = e.event_id
                                WHERE e.journal_id = %s ORDER BY c.changed_date DESC;""", (journal_id,))
            changes = cursor.fetchall()
    return render_template('changelog.html', changes=changes)


# Blueprint setup
bp = Blueprint('user', __name__)

# Allowed file extensions for image uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Support request submission route

@app.route('/support', methods=['GET', 'POST'])
def support():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    print(session['status'])
    if session.get('status') in ['ban_share', 'ban_all']:
        flash('Access denied. Your account is restricted from submitting support requests.', 'danger')
        return redirect(user_home_url()) # or homepage

    if request.method == 'POST':
        try:

            request_type = request.form['request_type']
            title = request.form['title'].strip()
            description = request.form['description'].strip()
            user_id = session['user_id']
            image_list = []

            # 验证表单输入
            if request_type not in ['Help', 'Bug']:
                flash('Invalid request type.', 'danger')
                return redirect(url_for('support'))
            if not title or len(title) > 100:
                flash('Title is required and must be 100 characters or less.', 'danger')
                return redirect(url_for('support'))
            if not description or len(description) > 1000:
                flash('Description is required and must be 1000 characters or less.', 'danger')
                return redirect(url_for('support'))

            # 处理图片上传
            if 'images' in request.files:
                files = request.files.getlist('images')
                for file in files:
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        image_list.append('uploads/' + filename)
                    elif file.filename != '':
                        flash('Invalid file type for one or more images.', 'danger')
                        return redirect(url_for('support'))

            # 插入 support_requests 表
            with db.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO support_requests (user_id, request_type, title, description, images, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ''', (user_id, request_type, title, description, ','.join(image_list) if image_list else None, 'New'))

            flash('Your support request has been submitted successfully!', 'success')
            return redirect(url_for('support'))

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'danger')
            app.logger.error(f'Support route error: {str(e)}', exc_info=True)
            return redirect(url_for('support'))

    return render_template('support.html')

# List all user support requests
@app.route('/support/requests', methods=['GET'])
def support_requests():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    try:
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT request_id, title, request_type, status, created_at
                FROM support_requests
                WHERE user_id = %s
                ORDER BY created_at DESC
            ''', (user_id,))
            requests = cursor.fetchall()
        return render_template('support_requests.html', requests=requests)
    except Exception as e:
        flash(f'Error fetching requests: {str(e)}', 'danger')
        app.logger.error(f'Support requests error: {str(e)}', exc_info=True)
        return redirect(url_for('support'))
    

# View request details and add replies
@app.route('/support/request/<int:request_id>', methods=['GET', 'POST'])
def support_request_detail(request_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    try:
        with db.get_cursor() as cursor:
            # Fetch request details
            cursor.execute('''
                SELECT request_id, user_id, request_type, title, description, images, status, created_at, owner_id
                FROM support_requests
                WHERE request_id = %s AND user_id = %s
            ''', (request_id, user_id))
            request_data = cursor.fetchone()

            if not request_data:
                flash('Request not found or you do not have access.', 'danger')
                return redirect(url_for('support_requests'))

            # Fetch replies
            cursor.execute('''
                SELECT reply_id, user_id, reply_text, created_at
                FROM replies
                WHERE request_id = %s
                ORDER BY created_at ASC
            ''', (request_id,))
            replies = cursor.fetchall()

            if request.method == 'POST':
                reply_text = request.form['reply_text'].strip()
                if not reply_text or len(reply_text) > 1000:
                    flash('Reply is required and must be 1000 characters or less.', 'danger')
                    return redirect(url_for('support_request_detail', request_id=request_id))

                if request_data['status'] == 'Resolved':
                    flash('Cannot add replies to a Resolved request.', 'danger')
                    return redirect(url_for('support_request_detail', request_id=request_id))

                # Insert reply
                cursor.execute('''
                    INSERT INTO replies (request_id, user_id, reply_text, created_at)
                    VALUES (%s, %s, %s, NOW())
                ''', (request_id, user_id, reply_text))
                flash('Reply added successfully!', 'success')
                return redirect(url_for('support_request_detail', request_id=request_id))

        return render_template('support_request_detail.html', request=request_data, replies=replies)

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        app.logger.error(f'Request detail error: {str(e)}', exc_info=True)
        return redirect(url_for('support_requests'))
    

# Support staff request detail and reply/status update route
@app.route('/support/staff-request/<int:request_id>', methods=['GET', 'POST'])
def support_staff_request_detail(request_id):
    if 'loggedin' not in session or not is_staff():
        flash('You must be a staff member to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT sr.request_id, sr.user_id, sr.request_type, sr.title, sr.description, sr.images, 
                       sr.status, sr.created_at, sr.owner_id, COALESCE(u.username, 'Unknown') AS submitter_username
                FROM support_requests sr
                LEFT JOIN users u ON sr.user_id = u.user_id
                WHERE sr.request_id = %s
            ''', (request_id,))
            request_data = cursor.fetchone()

            if not request_data:
                flash('Request not found.', 'danger')
                return redirect(url_for('support_staff_queue'))

            cursor.execute('''
                SELECT r.reply_id, r.user_id, r.reply_text, r.created_at, COALESCE(u.username, 'Unknown') AS reply_username
                FROM replies r
                LEFT JOIN users u ON r.user_id = u.user_id
                WHERE r.request_id = %s
                ORDER BY r.created_at ASC
            ''', (request_id,))
            replies = cursor.fetchall()

            if request.method == 'POST':
                owner_id = int(request_data['owner_id']) if request_data['owner_id'] is not None else None
                user_id = int(session['user_id'])

                app.logger.info(f'POST request: _action={request.form.get("_action")}, status={request.form.get("status")}')

                if request.form.get('_action') == 'reply':
                    if owner_id != user_id:
                        flash('Only the assigned staff member can reply.', 'danger')
                        return redirect(url_for('support_staff_request_detail', request_id=request_id))

                    if request_data['status'] == 'Resolved':
                        flash('Cannot add replies to a Resolved request.', 'danger')
                        return redirect(url_for('support_staff_request_detail', request_id=request_id))

                    reply_text = request.form.get('reply_text', '').strip()
                    if not reply_text:
                        flash('Reply cannot be empty.', 'danger')
                        return redirect(url_for('support_staff_request_detail', request_id=request_id))
                    if len(reply_text) > 1000:
                        flash('Reply must be 1000 characters or less.', 'danger')
                        return redirect(url_for('support_staff_request_detail', request_id=request_id))

                    cursor.execute('''
                        INSERT INTO replies (request_id, user_id, reply_text, created_at)
                        VALUES (%s, %s, %s, NOW())
                    ''', (request_id, user_id, reply_text))
                    flash('Reply added successfully!', 'success')
                    return redirect(url_for('support_staff_request_detail', request_id=request_id))

                elif request.form.get('_action') == 'update_status':
                    new_status = request.form.get('status')
                    valid_statuses = ['In Progress', 'Stalled', 'Resolved']

                    app.logger.info(f'Valid statuses: {valid_statuses}, Requested status: {new_status}')

                    if new_status not in valid_statuses:
                        flash('Invalid status selected.', 'danger')
                        return redirect(url_for('support_staff_request_detail', request_id=request_id))

                    cursor.execute('''
                        UPDATE support_requests
                        SET status = %s
                        WHERE request_id = %s
                    ''', (new_status, request_id))
                    flash(f'Status updated to {new_status} successfully!', 'success')
                    return redirect(url_for('support_staff_request_detail', request_id=request_id))

        return render_template('support_staff_request_detail.html', request=request_data, replies=replies)

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        app.logger.error(f'Staff request detail error: {str(e)}', exc_info=True)
        return redirect(url_for('support_staff_queue'))
    



@app.route('/journal/<int:journal_id>')
def view_journal(journal_id):
    if 'loggedin' not in session:
        return render_template('access_denied.html'), 403

    with db.get_cursor() as cursor:
        # Get journal info
        cursor.execute('''
            SELECT j.*, u.username
            FROM journals j
            JOIN users u ON j.user_id = u.user_id
            WHERE j.journal_id = %s AND j.j_status = 'public'
        ''', (journal_id,))
        journal = cursor.fetchone()

        if not journal:
            flash("Journal not found or not public.", "warning")
            return redirect(url_for('allpublicjournal'))

        # Get related events
        cursor.execute('SELECT * FROM events WHERE journal_id = %s', (journal_id,))
        events = cursor.fetchall()

        # Compute durations and find first image
        first_event_image = None
        for event in events:
            if event['e_enddatetime'] and event['e_startdatetime']:
                duration = round((event['e_enddatetime'] - event['e_startdatetime']).total_seconds() / 3600, 1)
                event['duration'] = duration
            else:
                event['duration'] = 0

            if not first_event_image and event.get('e_image'):
                first_event_image = event['e_image']

        journal['events'] = events
        journal['cover'] = journal['cover_image'] or first_event_image

    return render_template('journal_detail.html', journal=journal)

# Support staff update status (for queue page)
@app.route('/support/staff-update-status/<int:request_id>', methods=['POST'])
def support_staff_update_status(request_id):
    if 'loggedin' not in session or not is_staff():
        flash('You must be a staff member to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT status FROM support_requests WHERE request_id = %s
            ''', (request_id,))
            request_data = cursor.fetchone()

            if not request_data:
                flash('Request not found.', 'danger')
                return redirect(url_for('support_staff_queue'))

            new_status = request.form.get('status')
            valid_statuses = ['In Progress', 'Stalled', 'Resolved']

            app.logger.info(f'Update status: request_id={request_id}, valid_statuses={valid_statuses}, new_status={new_status}')

            if new_status not in valid_statuses:
                flash('Invalid status selected.', 'danger')
                return redirect(url_for('support_staff_queue'))

            cursor.execute('''
                UPDATE support_requests
                SET status = %s
                WHERE request_id = %s
            ''', (new_status, request_id))
            flash(f'Status updated to {new_status} successfully!', 'success')
            return redirect(url_for('support_staff_queue'))

    except Exception as e:
        flash(f'Error updating status: {str(e)}', 'danger')
        app.logger.error(f'Staff update status error: {str(e)}', exc_info=True)
        return redirect(url_for('support_staff_queue'))


# Support staff queue
@app.route('/support/staff-queue')
def support_staff_queue():
    if 'loggedin' not in session or not is_staff():
        flash('You must be a staff member to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        with db.get_cursor() as cursor:
            # Fetch requests with submitter and owner usernames
            cursor.execute('''
                SELECT
    sr.request_id,
    sr.title,
    sr.request_type,
    sr.status,
    sr.created_at,
    u.username AS submitter_username,
    ou.username AS owner_username,
    sr.owner_id,
    CASE
        WHEN u.subscription_expiry IS NOT NULL AND u.subscription_expiry >= CURRENT_DATE THEN TRUE
        ELSE FALSE
    END AS is_premium,
    CASE
        WHEN u.role IN ('editor', 'admin', 'support_tech') THEN TRUE
        ELSE FALSE
    END AS is_staff
FROM support_requests sr
LEFT JOIN users u ON sr.user_id = u.user_id
LEFT JOIN users ou ON sr.owner_id = ou.user_id
ORDER BY sr.created_at DESC;

            ''')
            requests = cursor.fetchall()

            # Fetch staff list for assign dropdown
            cursor.execute('''
                SELECT user_id, username
                FROM users
                WHERE role IN ('editor', 'admin', 'support_tech')
                ORDER BY username
            ''')
            staff = cursor.fetchall()
            cursor.execute('''SELECT
                u.*,
                CASE
                    WHEN u.subscription_expiry IS NOT NULL AND u.subscription_expiry >= CURRENT_DATE THEN TRUE
                    ELSE FALSE
                END AS is_premium,
                CASE
                    WHEN u.role IN ('editor', 'admin', 'support_user') THEN TRUE
                    ELSE FALSE
                END AS is_staff
            FROM users u;
            ''')
            # priority=cursor.fetchall()
        return render_template('support_staff_queue.html', requests=requests, staff=staff,)
    except Exception as e:
        flash(f'Error loading staff queue: {str(e)}', 'danger')
        app.logger.error(f'Staff queue error: {str(e)}', exc_info=True)
        return redirect(url_for('support'))

@app.route('/support/view-users', methods=['GET'])
def support_view_users():
    if session['role'] !='support_tech':
        flash('Unauthorized access.', 'danger')
        return redirect(user_home_url()) # or homepage

    search = request.args.get('search', '').strip()

    try:
        with db.get_cursor() as cursor:
            # Query for user profiles and subscription info
            cursor.execute('''
                SELECT u.user_id, u.username, u.email, u.first_name, u.last_name, 
                       u.user_status, u.role, us.plan_name, us.start_date, us.end_date
                FROM users u
                LEFT JOIN user_subscriptions us ON u.user_id = us.user_id
                WHERE u.username LIKE %s OR u.email LIKE %s
                ORDER BY u.username
            ''', (f"%{search}%", f"%{search}%"))
            users = cursor.fetchall()

        return render_template('support_users.html', users=users, search=search)

    except Exception as e:
        flash(f'Error loading user data: {str(e)}', 'danger')
        app.logger.error(f'Support user view error: {str(e)}', exc_info=True)
        return redirect(url_for('support'))


@app.route('/support/staff-take/<int:request_id>', methods=['POST'])
def support_staff_take(request_id):
    if 'loggedin' not in session or not is_staff():
        flash('You must be a staff member to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        with db.get_cursor() as cursor:
            # Check if request exists and is unassigned
            cursor.execute('''
                SELECT owner_id, status FROM support_requests WHERE request_id = %s
            ''', (request_id,))
            request_data = cursor.fetchone()

            if not request_data:
                flash('Request not found.', 'danger')
                return redirect(url_for('support_staff_queue'))
            if request_data['owner_id']:
                flash('Request is already assigned.', 'danger')
                return redirect(url_for('support_staff_queue'))
            if request_data['status'] == 'Resolved':
                flash('Cannot take a resolved request.', 'danger')
                return redirect(url_for('support_staff_queue'))

            # Update owner and status
            cursor.execute('''
                UPDATE support_requests
                SET owner_id = %s, status = %s
                WHERE request_id = %s
            ''', (session['user_id'], 'In Progress', request_id))

        flash('Request taken successfully!', 'success')
        return redirect(url_for('support_staff_queue'))

    except Exception as e:
        flash(f'Error taking request: {str(e)}', 'danger')
        app.logger.error(f'Staff take request error: {str(e)}', exc_info=True)
        return redirect(url_for('support_staff_queue'))

@app.route('/support/staff-assign/<int:request_id>', methods=['POST'])
def support_staff_assign(request_id):
    if 'loggedin' not in session or not is_staff():
        flash('You must be a staff member to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        assignee_id = request.form.get('assignee_id')
        if not assignee_id:
            flash('Please select a staff member to assign.', 'danger')
            return redirect(url_for('support_staff_queue'))

        with db.get_cursor() as cursor:
            # Check if request exists and is unassigned
            cursor.execute('''
                SELECT owner_id, status FROM support_requests WHERE request_id = %s
            ''', (request_id,))
            request_data = cursor.fetchone()

            if not request_data:
                flash('Request not found.', 'danger')
                return redirect(url_for('support_staff_queue'))
            if request_data['owner_id']:
                flash('Request is already assigned.', 'danger')
                return redirect(url_for('support_staff_queue'))
            if request_data['status'] == 'Resolved':
                flash('Cannot assign a resolved request.', 'danger')
                return redirect(url_for('support_staff_queue'))

            # Verify assignee is a staff member
            cursor.execute('''
                SELECT user_id FROM users WHERE user_id = %s AND role IN ('Editor', 'Admin', 'Support Tech')
            ''', (assignee_id,))
            assignee = cursor.fetchone()
            if not assignee:
                flash('Invalid staff member selected.', 'danger')
                return redirect(url_for('support_staff_queue'))

            # Update owner and status
            cursor.execute('''
                UPDATE support_requests
                SET owner_id = %s, status = %s
                WHERE request_id = %s
            ''', (assignee_id, 'In Progress', request_id))

        flash('Request assigned successfully!', 'success')
        return redirect(url_for('support_staff_queue'))

    except Exception as e:
        flash(f'Error assigning request: {str(e)}', 'danger')
        app.logger.error(f'Staff assign request error: {str(e)}', exc_info=True)
        return redirect(url_for('support_staff_queue'))

# Support staff drop request
@app.route('/support/staff-drop/<int:request_id>', methods=['POST'])
def support_staff_drop(request_id):
    if 'loggedin' not in session or not is_staff():
        flash('You must be a staff member to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        with db.get_cursor() as cursor:
            cursor.execute('''
                SELECT owner_id, status FROM support_requests WHERE request_id = %s
            ''', (request_id,))
            request_data = cursor.fetchone()

            if not request_data:
                flash('Request not found.', 'danger')
                return redirect(url_for('support_staff_queue'))
            if request_data['owner_id'] != int(session['user_id']):
                flash('Only the assigned staff member can drop this request.', 'danger')
                return redirect(url_for('support_staff_queue'))
            if request_data['status'] == 'Resolved':
                flash('Cannot drop a resolved request.', 'danger')
                return redirect(url_for('support_staff_queue'))

            new_status = 'New' if request_data['status'] != 'Stalled' else 'Stalled'
            app.logger.info(f'Dropping request_id={request_id}, new_status={new_status}')

            cursor.execute('''
                UPDATE support_requests
                SET owner_id = NULL, status = %s
                WHERE request_id = %s
            ''', (new_status, request_id))

        flash('Request dropped successfully!', 'success')
        return redirect(url_for('support_staff_queue'))

    except Exception as e:
        flash(f'Error dropping request: {str(e)}', 'danger')
        app.logger.error(f'Staff drop request error: {str(e)}', exc_info=True)
        return redirect(url_for('support_staff_queue'))
