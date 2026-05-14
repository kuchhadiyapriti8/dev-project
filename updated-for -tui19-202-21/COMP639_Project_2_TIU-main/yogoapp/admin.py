from yogoapp import app
from yogoapp import db
from flask import redirect, render_template, session, url_for,flash,request
from datetime import datetime, timedelta

@app.route('/admin/home')
def admin_home():
     """Admin Homepage endpoint.

     Methods:
     - get: Renders the homepage for the current admin user, or an "Access
          Denied" 403: Forbidden page if the current user has a different role.

     If the user is not logged in, requests will redirect to the login page.
     """
     if 'loggedin' not in session:
          print("No 'logeedin' in session:", session)
          return redirect(url_for('login'))
     elif session['role']!='admin':
          return render_template('access_denied.html'), 403

     return render_template('admin_home.html')


@app.route('/admin/usermanagement')
def user_management():
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role']!='admin':
         return render_template('access_denied.html'), 403

     with db.get_cursor() as cursor:
         cursor.execute('SELECT * FROM users')
         users = cursor.fetchall()
     
     
     return render_template('user_management.html', users=users)




@app.route('/alljournal')
def alljournal():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] not in ['admin', 'editor','support_tech']:
        return render_template('access_denied.html'), 403

    search_query = request.args.get('search', '').strip().lower()

    with db.get_cursor() as cursor:
        # Modify SQL query to filter journals based on the search query
        if search_query:
            cursor.execute('''
                SELECT j.*, u.username
                FROM journals j
                JOIN users u ON j.user_id = u.user_id
                WHERE j.j_status = 'public' 
               AND j.is_hidden = 0
                AND (LOWER(j.j_title) LIKE %s OR LOWER(j.j_description) LIKE %s)
                ORDER BY j.j_startdate DESC
            ''', (f'%{search_query}%', f'%{search_query}%'))
        else:
            cursor.execute('''
                SELECT j.*, u.username
                FROM journals j
                JOIN users u ON j.user_id = u.user_id
                WHERE j.j_status = 'public'
               AND j.is_hidden = 0
                ORDER BY j.j_startdate DESC
            ''')

        journals = cursor.fetchall()
        my_journey_is_empty = not bool(journals)

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

    return render_template('alljournal.html', journals=journals, my_journey_is_empty=my_journey_is_empty, search_query=search_query)

@app.route("/hide_journal/<int:journal_id>", methods=['POST'])
def hide_journal(journal_id):
    hidden_at = datetime.now()

    with db.get_cursor() as cursor:
        # Update journal to mark it hidden
        cursor.execute('''
            UPDATE journals 
            SET is_hidden = TRUE, hidden_by = %s, hidden_at = %s
            WHERE journal_id = %s
        ''', (session['user_id'], hidden_at, journal_id))
        flash('Journal has been successfully hidden.', 'warning')
    return redirect(url_for('alljournal'))
     
@app.route('/edit_journal/<int:journal_id>', methods=['POST'])
def edit_journal(journal_id):
    # Check if user is logged in and has admin/editor role
    if 'user_id' not in session or session.get('role') not in ['admin', 'editor']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('alljournal'))

    # Get updated data from the form
    new_title = request.form['j_title']
    new_description = request.form['j_description']

    # Update journal details in the database
    with db.get_cursor() as cursor:
        cursor.execute('''
            UPDATE journals 
            SET j_title = %s, j_description = %s 
            WHERE journal_id = %s
        ''', (new_title, new_description, journal_id))

    flash('Journal updated successfully.', 'success')
    return redirect(url_for('alljournal'))


@app.route('/admin/user/<int:user_id>')
def user_detail(user_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'admin':
        return render_template('access_denied.html'), 403

    with db.get_cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
        user = cursor.fetchone()
        
        # Get admin plans for reward subscription
        cursor.execute('''
            SELECT * FROM subscription_plans 
            WHERE is_admin_grant = 1
            ORDER BY months ASC
        ''')
        admin_plans = cursor.fetchall()
    
    return render_template(
                          'user_detail.html', 
                          user=user, 
                          admin_plans=admin_plans,
                          available_roles=['traveller', 'editor', 'support_tech']
                          )


@app.route('/admin/user', methods=['GET', 'POST'])
def user_search():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    elif session['role'] != 'admin':
        return render_template('access_denied.html'), 403

    users = []
    search_query = request.form.get('search_query', '')
    with db.get_cursor() as cursor:
        if search_query:
            cursor.execute("""
                SELECT * FROM users 
                WHERE username LIKE %s OR first_name LIKE %s OR last_name LIKE %s OR email LIKE %s
            """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
    return render_template('user_management.html', users=users, search_query=search_query)


@app.route('/admin/change_role/<int:user_id>', methods=['POST'])
def change_role(user_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        return render_template('access_denied.html'), 403
    
    new_role = request.form.get('new_role')
    valid_roles = ['traveller', 'editor', 'support_tech']  # add support_tech
    
    if new_role not in valid_roles:
        flash('Invalid role selected', 'danger')
        return redirect(url_for('user_detail', user_id=user_id))
    
    with db.get_cursor() as cursor:
        cursor.execute("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
        if int(user_id)==session['user_id']:
                session['role']= new_role
    flash('User role updated successfully!', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/admin/change_status/<int:user_id>', methods=['POST'])
def change_status(user_id):
    if 'loggedin' not in session or session['role'] != 'admin' :
        return render_template('access_denied.html'), 403
    
    new_status = request.form.get('new_status')
    
    with db.get_cursor() as cursor:
        cursor.execute("UPDATE users SET user_status = %s WHERE user_id = %s", (new_status, user_id))
        if int(user_id)==session['user_id']:
            if new_status !='active':
                return redirect(url_for('logout'))

    flash('User status updated successfully!', 'success')
    return redirect(url_for('user_detail', user_id=user_id))

@app.route('/admin/reward_subscription/<int:user_id>', methods=['POST'])
def admin_reward_subscription(user_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        return render_template('access_denied.html'), 403
    
    plan_name = request.form.get('plan_name')
    if not plan_name:
        flash('Please select a plan.', 'error')
        return redirect(url_for('user_detail', user_id=user_id))
    
    with db.get_cursor() as cursor:

        cursor.execute('SELECT * FROM subscription_plans WHERE plan_name = %s', (plan_name,))
        plan = cursor.fetchone()
        
        if not plan:
            flash('Invalid subscription plan.', 'error')
            return redirect(url_for('user_detail', user_id=user_id))
        
        # get current active subscription if any
        cursor.execute('''
            SELECT * FROM user_subscriptions 
            WHERE user_id = %s 
            AND end_date > CURDATE()
            ORDER BY end_date DESC
            LIMIT 1
        ''', (user_id,))
        current_subscription = cursor.fetchone()
        
        # calculate dates
        start_date = datetime.now()
        if current_subscription:
            # if there's an active subscription, extend from its end date
            end_date = current_subscription['end_date']
            if plan['months'] == 12:
                start_date = current_subscription['end_date']
                end_date = end_date.replace(year=end_date.year + 1)
            else:
                start_date = current_subscription['end_date']
                end_date = current_subscription['end_date'] + timedelta(days=31 * plan['months'])
        else:
            # if no active subscription, start from today
            if plan['months'] == 12:
                end_date = start_date.replace(year=start_date.year + 1)
            else:
                end_date = start_date + timedelta(days=31 * plan['months'])
        
        # create new subscription
        cursor.execute('''
            INSERT INTO user_subscriptions 
            (user_id, plan_name, start_date, end_date, created_by_admin)
            VALUES (%s, %s, %s, %s, %s)
        ''', (user_id, plan['plan_name'], start_date, end_date,session['user_id']))
        # do not record payment
        # update user's subscription status
        cursor.execute('''
            UPDATE users 
            SET subscription_status = 'Premium', 
                subscription_expiry = %s 
            WHERE user_id = %s
        ''', (end_date, user_id))
        
        flash('Subscription rewarded successfully!', 'success')
        return redirect(url_for('user_detail', user_id=user_id))


@app.route('/admin/update_user/<int:user_id>', methods=['POST'])
def admin_update_user(user_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        return render_template('access_denied.html'), 403



    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        location = request.form['location']

        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT user_id FROM users 
                WHERE email = %s AND user_id != %s
            """, (email, user_id))
            existing_user = cursor.fetchone()

            if not existing_user:
                cursor.execute("""
                    UPDATE users 
                    SET username = %s, 
                        email = %s, 
                        first_name = %s, 
                        last_name = %s, 
                        location = %s
                    WHERE user_id = %s
                """, (username, email, first_name, last_name, location, user_id))

    return redirect(url_for('user_management'))


@app.route('/admin/remove_image/<int:user_id>', methods=['POST'])
def admin_remove_image(user_id):
    if 'loggedin' not in session or session['role'] != 'admin':
        return render_template('access_denied.html'), 403
        
    with db.get_cursor() as cursor:
        cursor.execute("UPDATE users SET profile_image = 'default.png' WHERE user_id = %s", (user_id,))
        flash('Profile photo removed successfully', 'success')
    
    return redirect(url_for('user_detail', user_id=user_id))





