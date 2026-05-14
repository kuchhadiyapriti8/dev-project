# from flask import Flask
# from flask_mysqldb import MySQL
# from flask_hashing import Hashing


# app = Flask(__name__)

# # Configuration
# # app.config['MYSQL_HOST'] = 'localhost'
# # app.config['MYSQL_USER'] = 'root'
# # app.config['MYSQL_PASSWORD'] = 'Password'
# # app.config['MYSQL_DB'] = 'my_db'
# app.secret_key = '1a2b3c4d5e6d7g8h9i10'

# # Initialize MySQL
# # mysql = MySQL(app)
# # hashing = Hashing(app)

# # Import blueprints
# from .admin import admin_blueprint
# from .auth import auth_blueprint
# from .member import member_blueprint

# # Register blueprints
# app.register_blueprint(admin_blueprint, url_prefix='/admin')
# app.register_blueprint(auth_blueprint, url_prefix='/auth')
# app.register_blueprint(member_blueprint, url_prefix='/member')

# app = Flask(__name__)

# DB_HOST = 'localhost'
# DB_USER = 'root'
# DB_PASSWORD = 'Password'
# DB_NAME = 'my_db'
# # Intialize MySQL
# mysql = MySQL(app)
# hashing = Hashing(app)

# db = MySQLdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
# cursor = db.cursor()
# # Change this to your secret key (can be anything, it's for extra protection)
# app.secret_key = '1a2b3c4d5e6d7g8h9i10'

# # Enter your database connection details below
# # app.config['MYSQL_HOST'] = 'localhost'
# # app.config['MYSQL_USER'] = 'root'
# # app.config['MYSQL_PASSWORD'] = 'Password' #Replace ******* with  your database password.
# # app.config['MYSQL_DB'] = 'my_db'


# # Intialize MySQL

# from .admin import *
# from .auth import *
# from .member import *


