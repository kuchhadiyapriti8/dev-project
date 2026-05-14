from yogoapp import app
from yogoapp import db
from flask import redirect, render_template, session, url_for
from datetime import datetime

@app.route('/traveller/home')
def traveller_home():
     
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['role'] != 'traveller':
          return render_template('access_denied.html'), 403

     journal_id = None
     show_reminder = False
     days_left = None
     print()
     with db.get_cursor() as cursor:
          # Get journal_id for current user
          cursor.execute("SELECT journal_id FROM journals WHERE user_id = %s", (session['user_id'],))
          journal = cursor.fetchone()
          if journal:
               journal_id = journal['journal_id']

          # Get subscription expiry date
          
          cursor.execute("SELECT subscription_expiry FROM users WHERE user_id = %s", (session['user_id'],))
          user = cursor.fetchone()
          if user and user['subscription_expiry']:
               try:
                    expiry_date = user['subscription_expiry']
                    if isinstance(expiry_date, str):  # In case it's a string
                         expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d")
                    today = datetime.today().date()
                    delta_days = (expiry_date - today).days
                    if 0 < delta_days <= 5:
                         show_reminder = True
                         days_left = delta_days
               except Exception:
                    pass  # Ignore any parsing issues silently

# The user isn't logged in with a customer account, so return an
          # "Access Denied" page instead. We don't do a redirect here, because
          # we're not sending them somewhere else: just delivering an
          # alternative page.
          # 
          # Note: the '403' below returns HTTP status code 403: Forbidden to the
          # browser, indicating that the user was not allowed to access the
          # requested page.

     return render_template(
        'traveller_home.html',
        journal_id=journal_id,
        show_reminder=show_reminder,
        days_left=days_left
    )