from flask import Flask,flash
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
    curr_date = cursor.fetchone()[0] 
    # curr_date = get_date().strftime("%Y-%m-%d")  # Format the date as YYYY-MM-DD
    session['curr_date'] = curr_date       
    return curr_date
@app.route("/")
def root():
        return redirect(url_for('home'))

####### Updated if statement with this line
@app.route("/home")
def home():
    # This line: 
    curr_date = get_date()
    # Replaces these lines:
    if 'curr_date' not in session:
        session.update({'curr_date': start_date})
    return render_template("home.html",curr_date=curr_date)

####### New function to reset the simulation back to the beginning - replaces reset_date() and clear_date()
##  NOTE: This requires fms-reset.sql file to be in the same folder as app.py
@app.route("/reset_date", methods=["POST"])
def reset_date():
    """Reset data to original state."""
    THIS_FOLDER = Path(__file__).parent.resolve()
    with open(THIS_FOLDER / 'fms-reset.sql', 'r') as f:
        mqstr = f.read()
        for qstr in mqstr.split(";"):
            cursor = getCursor()
            cursor.execute(qstr)
    
    # Commit changes and fetch the updated date
    db_connection.commit()
    get_date()

    flash("The database has been reset to the original state.", "success")
    return redirect(url_for('paddocks'))
 



# Route to display paddocks
@app.route("/paddocks", methods=["GET", "POST"])
def paddocks():
    cursor = getCursor()
    
    if request.method == "POST":
        # Handle the request to advance the current date
        cursor.execute("UPDATE curr_date SET curr_date = DATE_ADD(curr_date, INTERVAL 1 DAY);")
        db_connection.commit()
        flash("Current date advanced by one day!", "success")
        return redirect(url_for('paddocks'))

    # Fetch paddock details, mobs, and stock counts
    cursor.execute("""
        SELECT p.id, p.name, p.area, p.dm_per_ha, (p.area * p.dm_per_ha) AS total_dm,
               m.name AS mob_name, COUNT(s.id) AS stock_count
        FROM paddocks p
        LEFT JOIN mobs m ON p.id = m.paddock_id
        LEFT JOIN stock s ON m.id = s.mob_id
        GROUP BY p.id
        ORDER BY p.name ASC;
    """)
    paddocks = cursor.fetchall()
    
    cursor.close()
    db_connection.close()
    
    return render_template("paddocks.html", paddocks=paddocks)


@app.route("/add_paddock", methods=["GET", "POST"])
def add_paddock():
    if request.method == "POST":
        paddock_name = request.form['name']
        area = float(request.form['area'])  # Convert area to float for validation
        dm_per_ha = request.form['dm_per_ha']

        # Validate area to be greater than 1
        if area <= 1:
            flash("Area must be greater than 1 hectare.")
            return render_template("add_paddock.html")

        # Connect to the database
        cursor = getCursor()
        try:
            # Check if paddock name already exists
            cursor.execute("SELECT COUNT(*) FROM paddocks WHERE name = %s", (paddock_name,))
            result = cursor.fetchone()
            if result[0] > 0:
                flash("Paddock name already exists. Please choose a different name.")
                return render_template("add_paddock.html")

            # Insert new paddock into the database if validations pass
            query = "INSERT INTO paddocks (name, area, dm_per_ha) VALUES (%s, %s, %s)"
            cursor.execute(query, (paddock_name, area, dm_per_ha))
            db_connection.commit()
            flash("Paddock added successfully!")
            return redirect(url_for('paddocks'))
        except Exception as e:
            flash("Error adding paddock: " + str(e))
        finally:
            cursor.close()
            db_connection.close()

    return render_template("add_paddock.html")

@app.route("/edit_paddock/<int:paddock_id>", methods=["GET", "POST"])
def edit_paddock(paddock_id):
    cursor = getCursor()

    if request.method == "POST":
        paddock_name = request.form['name']
        area = request.form['area']
        dm_per_ha = request.form['dm_per_ha']

        # Update existing paddock in the database
        try:
            query = "UPDATE paddocks SET name=%s, area=%s, dm_per_ha=%s WHERE id=%s"
            cursor.execute(query, (paddock_name, area, dm_per_ha, paddock_id))
            db_connection.commit()
            flash("Paddock updated successfully!")
            return redirect(url_for('paddocks'))
        except Exception as e:
            flash("Error updating paddock: " + str(e))
        finally:
            cursor.close()
            db_connection.close()

    # Fetch existing paddock details for the form
    query = "SELECT name, area, dm_per_ha FROM paddocks WHERE id=%s"
    cursor.execute(query, (paddock_id,))
    paddock = cursor.fetchone()

    return render_template("edit_paddock.html", paddock=paddock)

@app.route("/advance_date", methods=["POST"])
def advance_date():
    cursor = getCursor()
    
    # Fetch the current date from the 'curr_date' table
    cursor.execute("SELECT curr_date FROM curr_date LIMIT 1;")
    curr_date_row = cursor.fetchone()
    curr_date = curr_date_row[0]

    # Advance the current date by one day
    new_date = curr_date + timedelta(days=1)
    
    # Update the current date in the database
    cursor.execute("UPDATE curr_date SET curr_date = %s;", (new_date,))
    session['curr_date']=new_date
    # Fetch all paddocks along with their details
    cursor.execute("""
        SELECT p.id, p.name, p.area, p.dm_per_ha, p.total_dm
        FROM paddocks p
        ORDER BY p.name ASC;
    """)
    paddocks = cursor.fetchall()

    # Update pasture values for each paddock
    for paddock in paddocks:
        paddock_id = paddock[0]  # paddock[0] is the ID
        area = paddock[2]
        dm_per_ha = paddock[3]
        total_dm = paddock[4]

        # Ensure total_dm is not None (initialize to 0 if None)
        if total_dm is None:
            total_dm = 0

        # Fetch the mob (if any) in the current paddock
        cursor.execute("""
            SELECT m.id, m.name, COUNT(s.id) AS num_stock
            FROM mobs m
            LEFT JOIN stock s ON s.mob_id = m.id
            WHERE m.paddock_id = %s
            GROUP BY m.id;
        """, (paddock_id,))
        mob = cursor.fetchone()

        if mob:  # If a mob exists in the paddock
            num_stock = mob[2]  # The third column is the number of stock
            # Calculate daily pasture consumption by the mob
            consumption = num_stock * stock_consumption_rate
        else:
            consumption = 0

        # Calculate daily pasture growth based on paddock area
        growth = area * pasture_growth_rate

        # Update total DM and DM/ha
        total_dm += growth - consumption
        dm_per_ha = total_dm / area

        # Update paddock values in the database
        cursor.execute("""
            UPDATE paddocks
            SET dm_per_ha = %s, total_dm = %s
            WHERE id = %s;
        """, (dm_per_ha, total_dm, paddock_id))

    # Commit the changes to the database
    db_connection.commit()

    flash("The current date has been advanced by one day. Pasture values have been updated.", "success")

    return redirect(url_for("paddocks"))



@app.route('/move_mob', methods=['GET', 'POST'])
def move_mob():
    cursor = getCursor()
    
    # Fetch mobs and their current paddock
    query_mobs = """
    SELECT m.id, m.name, IFNULL(p.name, 'Unassigned') AS paddock_name
    FROM mobs m
    LEFT JOIN paddocks p ON m.paddock_id = p.id
    ORDER BY m.name;
    """
    cursor.execute(query_mobs)
    mobs_data = cursor.fetchall()

    # Fetch all available paddocks (those without a mob assigned)
    query_paddocks = """
    SELECT p.id, p.name 
    FROM paddocks p 
    LEFT JOIN mobs m ON m.paddock_id = p.id 
    WHERE m.id IS NULL 
    ORDER BY p.name;
    """
    cursor.execute(query_paddocks)
    paddocks_data = cursor.fetchall()

    if request.method == 'POST':
        # Process the form to move mobs to new paddocks
        for mob in mobs_data:
            mob_id = mob[0]
            new_paddock_id = request.form.get(f'new_paddock_{mob_id}')
            
            # If a new paddock is selected, update the mob's paddock
            if new_paddock_id:
                query_update = "UPDATE mobs SET paddock_id = %s WHERE id = %s;"
                cursor.execute(query_update, (new_paddock_id, mob_id))
                db_connection.commit()
                flash(f"Mob {mob[1]} has been moved to a new paddock.")

        return redirect(url_for('move_mob'))

    return render_template('move_mob.html', mobs_data=mobs_data, paddocks_data=paddocks_data)

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


def get_mob_data():
    cursor = getCursor()

    # Query to get mob information
    query_mobs = """
    SELECT m.id AS mob_id, m.name AS mob_name, COUNT(s.id) AS stock_count, AVG(s.weight) AS avg_weight
    FROM mobs m
    LEFT JOIN stock s ON m.id = s.mob_id
    GROUP BY m.id
    ORDER BY m.name ASC;
    """
    cursor.execute(query_mobs)
    mobs = cursor.fetchall()  # Fetching all mobs data

    # Get stock details by mob (ID, age in years, dob, and weight)
    fms_date = get_date()  # Fetch the current date for calculating age
    query_stock = """
    SELECT s.mob_id, s.id, TIMESTAMPDIFF(YEAR, s.dob, %s) AS age_years, s.dob, s.weight
    FROM stock s
    ORDER BY s.mob_id ASC, s.id ASC;
    """
    cursor.execute(query_stock, (fms_date,))
    stock_data = cursor.fetchall()  # Fetching stock details

    # Organize stock data by mob_id
    stock_by_mob = {mob[0]: [] for mob in mobs}  # Initialize empty list for each mob_id

    for stock in stock_data:
        mob_id = stock[0]  # Get the mob_id from stock data
        stock_by_mob[mob_id].append({
            "id": stock[1],
            "age_years": stock[2],
            "dob": stock[3],
            "weight": stock[4]
        })

    return mobs, stock_by_mob



@app.route('/stock_by_mob')
def stock_by_mob():
    mobs_data, stock_by_mob = get_mob_data()

    return render_template('stock.html', mobs_data=mobs_data, stock_by_mob=stock_by_mob)


if __name__ == '__main__':
    app.run(debug=True)



