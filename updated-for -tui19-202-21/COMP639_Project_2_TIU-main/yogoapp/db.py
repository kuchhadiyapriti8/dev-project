"""Implements simple MySQL database connectivity for a Flask web app.

This approach is based on the "Define and Access the Database" Flask
tutorial [1], adapted to use MySQL with connection pooling. It gives you an
easy way to request a database connection or cursor while processing a Flask
request, and gives you access to that connection from anywhere in your app
(including other functions or modules) until the request is complete.

Usage:
------
When initialising your Flask application, call `init_db` passing in your
`Flask` application object and database connection details:
```
>>> app = Flask(__name__)
>>> db.init_db(app, 'username', 'password', 'host', 'database')
```

Then, while handling a Flask request you can get a database connection
specific to that request by calling:
```
>>> db = db.get_db()
>>> # Your database code here...
```

If you need a new cursor, you can call:
```
>>> cursor = db.get_cursor()
>>> # Your database code here...
>>> cursor.close()
```

Alternatively, consider using a `with` block to ensure that the cursor is
automatically closed at the end of your query:
```
>>> with get_cursor() as cursor:
>>>     # Your query here...
```

Note that you don't have to close the database connection returned by
`get_db()` as it will be closed automatically at the end of the Flask request.
However, you should ensure that you close all cursors: this includes any
created by the `get_cursor()` function, and any you create manually using the
database connection.

References:
-----------
    [1] https://flask.palletsprojects.com/en/stable/tutorial/database/
"""
from flask import Flask, g  
from mysql.connector.pooling import MySQLConnectionPool

# Pool of reusable database connections (created when calling `init_db`).
connection_pool: MySQLConnectionPool

def init_db(app: Flask, user: str, password: str, host: str, database: str,
            pool_name: str = "flask_db_pool", autocommit: bool = True):
    """Sets up a MySQL connection pool for the specified Flask app.

    This must be called once while initialising your Flask web app, before any
    other `db` module functions are called.

    Args:
        app: The `Flask` application to set up database connectivity for.
        user: Username used to connect to the MySQL server.
        password: Password used to connect to the MySQL server.
        host: Host name or IP address of the MySQL server.
        database: Name of the database to connect to on the MySQL server.
        pool_name: Name of the pool to create (default `flask_db_pool`).
        autocommit: Whether or not to enable auto-commit (default `True`) .
    """
    # Create a pool of reusable database connections.
    global connection_pool
    connection_pool = MySQLConnectionPool(
        user=user,
        password=password,
        host=host,
        database=database,
        pool_name=pool_name,
        autocommit=autocommit)

    # Register `close_db()` to run every time the application context is torn
    # down at the end of a Flask request, ensuring that any database connection
    # using during that request gets released back into the pool.
    app.teardown_appcontext(close_db)

def get_db():
    if 'db' not in g:
        g.db = connection_pool.get_connection()
    
    return g.db

def get_cursor():
    return get_db().cursor(dictionary=True,buffered=True)

def close_db(exception = None):
    db = g.pop('db', None)
    
    if db is not None:
        db.close()