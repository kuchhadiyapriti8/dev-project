
from flask import Flask

app = Flask(__name__)

app.secret_key = 'YOGO Secret Key'

# Set up database connection.
from yogoapp import connect
from yogoapp import db
db.init_db(app, connect.dbuser, connect.dbpass, connect.dbhost, connect.dbname)

# Include all modules that define our Flask route-handling functions.
from yogoapp import user
from yogoapp import traveller
from yogoapp import editor
from yogoapp import admin