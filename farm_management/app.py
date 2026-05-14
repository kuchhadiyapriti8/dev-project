from flask import Flask
from flask import render_template
from flask import request
from flask import redirect 
from flask import url_for
from flask import session
from datetime import date, datetime, timedelta
import mysql.connector
import connect

####### Required for the reset function to work both locally and in PythonAnywhere
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'COMP636 S2'

start_date = datetime(2024,10,29)
pasture_growth_rate = 65    #kg DM/ha/day
stock_consumption_rate = 14 #kg DM/animal/day


db_connection = None

def getCursor():
    """Gets a new dictionary cursor for the database.
    If necessary, a new database connection is created here and used for all
    subsequent to getCursor()."""
    global db_connection
 
    if db_connection is None or not db_connection.is_connected():
        db_connection = mysql.connector.connect(user=connect.dbuser, \
            password=connect.dbpass, host=connect.dbhost,
            database=connect.dbname, autocommit=True)
       
    cursor = db_connection.cursor(buffered=False)   # returns a list
    # cursor = db_connection.cursor(dictionary=True, buffered=False)  # use a dictionary cursor if you prefer
    return cursor

####### New function - reads the date from the new database table
def get_date():
    cursor = getCursor()        
    qstr = "select curr_date from curr_date;"  
    cursor.execute(qstr)        
    curr_date = cursor.fetcho
    # ne()[0]        
    return curr_date

####### Updated if statement with this line
@app.route("/")
def home():
    # This line: 
    curr_date = get_date()
    # Replaces these lines:
    # if 'curr_date' not in session:
    #     session.update({'curr_date': start_date})
    return render_template("home.html", curr_date=curr_date)

####### New function to reset the simulation back to the beginning - replaces reset_date() and clear_date()
##  NOTE: This requires fms-reset.sql file to be in the same folder as app.py
@app.route("/reset")
def reset():
    """Reset data to original state."""
    THIS_FOLDER = Path(__file__).parent.resolve()
    with open(THIS_FOLDER / 'fms-reset.sql', 'r') as f:
        mqstr = f.read()
        for qstr in mqstr.split(";"):
            cursor = getCursor()
            cursor.execute(qstr)
    get_date()
    return redirect(url_for('paddocks'))  

# @app.route("/mobs")
# def mobs():
#     """List the mob details (excludes the stock in each mob)."""
#     cursor = getCursor()        
#     qstr = "select id, name from mobs;" 
#     cursor.execute(qstr)        
#     mobs = cursor.fetchall()        
#     return render_template("mobs.html", mobs=mobs)  
@app.route("/paddocks", methods=["GET", "POST"])
def paddocks():
    cursor = getCursor()
    
    # Fetch paddock details, including mob and stock info, sorted alphabetically by paddock name
    query = """
        SELECT p.id, p.name, p.dm_per_ha, p.area, p.dm_per_ha * p.area AS total_dm,
               m.name AS mob_name, 
               (SELECT COUNT(s.id) FROM stock s WHERE s.mob_id = m.id) AS stock_count
        FROM paddocks p
        LEFT JOIN mobs m ON p.id = m.paddock_id
        ORDER BY p.name ASC
    """
    cursor.execute(query)
    paddocks_data = cursor.fetchall()

    # Handle form submission to add new paddock
    if request.method == "POST":
        paddock_name = request.form['name']
        area = float(request.form['area'])
        dm_per_ha = float(request.form['dm_per_ha'])
        
        insert_query = """
            INSERT INTO paddocks (name, area, dm_per_ha) 
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (paddock_name, area, dm_per_ha))
        return redirect(url_for('paddocks'))

    return render_template("paddocks.html", paddocks=paddocks_data)


@app.route("/paddocks/edit/<int:id>", methods=["GET", "POST"])
def edit_paddock(id):
    cursor = getCursor()

    if request.method == "POST":
        name = request.form['name']
        area = float(request.form['area'])
        dm_per_ha = float(request.form['dm_per_ha'])
        
        update_query = """
            UPDATE paddocks 
            SET name=%s, area=%s, dm_per_ha=%s 
            WHERE id=%s
        """
        cursor.execute(update_query, (name, area, dm_per_ha, id))
        return redirect(url_for('paddocks'))
    
    query = "SELECT * FROM paddocks WHERE id=%s"
    cursor.execute(query, (id,))
    paddock = cursor.fetchone()
    
    return render_template("edit_paddock.html", paddock=paddock)

@app.route("/paddocks/next_day", methods=["POST"])
def next_day():
    """Move to the next day and update pasture values."""
    cursor = getCursor()

    # Update current date
    cursor.execute("UPDATE curr_date SET curr_date = curr_date + INTERVAL 1 DAY")
    
    # Update pasture values for all paddocks
    cursor.execute("""
        UPDATE paddocks 
        SET dm_per_ha = dm_per_ha + (area * %s) - (SELECT SUM(stock_count) * %s FROM mobs WHERE paddock_id=paddocks.id)
    """, (pasture_growth_rate, stock_consumption_rate))

    return redirect(url_for('paddocks')) 

@app.route("/move_mob", methods=["GET", "POST"])
def move_mob():
    cursor = getCursor()

    if request.method == "POST":
        # Process the move mob action
        mobs_data = get_mobs_with_paddocks(cursor)
        paddocks = get_paddocks(cursor)

        for mob in mobs_data:
            mob_name = mob[0]
            new_paddock = request.form.get(f'paddock_for_{mob_name}')

            # Check if the selected paddock already has a mob
            qstr_check = "SELECT id FROM mobs WHERE paddock_id = %s"
            cursor.execute(qstr_check, (new_paddock,))
            occupied_mob = cursor.fetchone()

            if occupied_mob:
                # Paddock is occupied, show error (could also be flashed to the user)
                print(f"Paddock {new_paddock} is already occupied!")
                continue

            # Update the mob's paddock
            qstr_update = "UPDATE mobs SET paddock_id = %s WHERE name = %s"
            cursor.execute(qstr_update, (new_paddock, mob_name))

        return redirect(url_for("mobs"))

    # For GET requests, display the form
    mobs_data = get_mobs_with_paddocks(cursor)
    paddocks = get_paddocks(cursor)
    return render_template("move_mob.html", mobs_data=mobs_data, paddocks=paddocks)

# Helper functions
def get_mobs_with_paddocks(cursor):
    qstr = """
        SELECT mobs.name, paddocks.name
        FROM mobs
        JOIN paddocks ON mobs.paddock_id = paddocks.id
    """
    cursor.execute(qstr)
    return cursor.fetchall()

def get_paddocks(cursor):
    qstr = "SELECT id, name FROM paddocks"
    cursor.execute(qstr)
    return cursor.fetchall()


@app.route("/mobs")
def mobs():
    cursor = getCursor()
    # Query to fetch mobs and their associated paddock names
    qstr = """
        SELECT mobs.name, paddocks.name
        FROM mobs
        JOIN paddocks ON mobs.paddock_id = paddocks.id
    """
    cursor.execute(qstr)
    mobs_data = cursor.fetchall()  # Fetch all results
    return render_template("mobs.html", mobs_data=mobs_data)

@app.route('/stock')
def stock():
    cursor = getCursor()

    # Query to get mobs, paddocks, stock count, and average weight
    mob_query = """
        SELECT mobs.name AS mob_name, paddocks.name AS paddock_name,
               COUNT(stock.id) AS stock_count, AVG(stock.weight) AS avg_weight
        FROM mobs
        JOIN paddocks ON mobs.paddock_id = paddocks.id
        LEFT JOIN stock ON stock.mob_id = mobs.id
        GROUP BY mobs.name, paddocks.name
        ORDER BY mobs.name
    """
    cursor.execute(mob_query)
    mobs_data = cursor.fetchall()  # Fetch all mobs and their paddocks

    # Query to get stock details, including ID and age, grouped by mob
    stock_query = """
        SELECT stock.id AS stock_id, stock.mob_id, stock.date_of_birth,
               TIMESTAMPDIFF(YEAR, stock.date_of_birth, CURDATE()) AS age_years
        FROM stock
        ORDER BY stock.mob_id, stock.id
    """
    cursor.execute(stock_query)
    stock_data = cursor.fetchall()  # Fetch all stock details

    # Group stock by mob
    stock_by_mob = {}
    for stock in stock_data:
        mob_id = stock[1]  # mob_id is the second field in stock_data
        if mob_id not in stock_by_mob:
            stock_by_mob[mob_id] = []
        stock_by_mob[mob_id].append({
            'id': stock[0],
            'age_years': stock[3]
        })

    # Pass mobs_data and stock_by_mob to the template
    return render_template('stock.html', mobs_data=mobs_data, stock_by_mob=stock_by_mob)



