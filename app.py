from flask import Flask, request, jsonify, make_response, render_template, session, redirect, url_for
import sqlite3 # databasing software
from functools import wraps # decorators
import jwt # auth
from datetime import datetime, timedelta # sets jwt expiry
import json # auth checking
import csv # for db uploading
from io import StringIO # done for csv conversion

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# SQLite database connection
connect = sqlite3.connect('database.db', check_same_thread=False)
connect.row_factory = sqlite3.Row
cursor = connect.cursor()



# User roles and their corresponding permissions
ROLES = {
    'root': ['read requests', 'write requests', 'gen requests', 'gen reports', 'read reports', 'config'],
    'admin': ['read requests', 'write requests', 'gen requests', 'gen reports', 'read reports','edit schedule'],
    'eUser': ['read requests', 'write requests', 'gen requests', 'gen reports', 'read reports'],
    'attendance': ['read reports', 'gen reports'],
    'user': ['requests']
}

def db_upload_table(database,):
    """
    quick function for connecting, and uploading a db 
    """

    return

def authenticate(username, password):
    """
    Authenticates the user against the SQLite database.
    Returns the user's role if authentication is successful, None otherwise.
    """
    query = "SELECT * FROM users WHERE username=? AND password=?"
    cursor.execute(query, (username, password))
    user = cursor.fetchone()

    if user:
        return user['role']
    else:
        return None


def create_jwt(username, role):
    """
    Creates a JWT token with the user's username, role, and expiration time.
    """
    payload = {
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=1)  # Experation Time Set here (Make a varible later?)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


def decode_jwt(token):
    """
    Decodes the JWT token and returns the payload.
    Returns None if the token is invalid.
    """
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        print("session expired. please try again.")
        return None


def has_permission(permission):
    """
    Decorator function to check if the user has the required permission.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            session_token = session.get('token')
            if session_token:
                payload = decode_jwt(session_token)
                if payload and 'role' in payload:
                    role = payload['role']
                    if permission in ROLES.get(role, []):
                        return f(*args, **kwargs)
            return 'Unauthorized. Please contact your network administrator if you think there has been a mistake.'
        return wrapper
    return decorator

# ALL app routes

#home route
@app.route('/', methods=['GET'])
def home():
    """
    Sends users to login if not already logged in, then sends them to respective dashboard based on privilages.
    
    """
    token = session.get('token')
    if token: # checks to see if there even is a token
       if decode_jwt(token=token): # checks for any jwt errors. if any, it returns none from
            #
            role = decode_jwt(token=token).get('role')# decodes token and gets key 'role' from token json
            if role == 'user':
                return 'user'
            elif role == 'attendance':
                return 'attendance'
            elif role == 'admin':
                return 'admin'
            elif role == 'eUser':
                return 'Elivated User'
            elif role == 'root':
                return 'root user'
            else:
                return 'Error! No Role!'
            #need to add auto send to right panel based on if admin or teacher


            return 'all good!'
       
    return redirect('/login')


# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders the login page and authenticates the user and returns a JWT token.
    """
    if request.method == 'POST':
        # Handle form submission
        username = request.form.get('username')
        password = request.form.get('password')

        # Authentication logic
        if authenticate(username, password):
            role = authenticate(username, password)
            if role:
                token = create_jwt(username, role)
                decode_jwt(token=token)
                session['token'] = token  # Save the JWT token to the session
                response = 'Login Sucessfull! Token is ' + token
                return redirect('/')
                
        else:
            error_message = "Invalid credentials. Please try again."

        return render_template('login.html', error_message=error_message)
    else:
        # Render the login page
        return render_template('login.html', error_message='')


# Logout Route. Removes jwt sessiondata. might need to use form in future.
@app.route('/logout', methods=['GET','POST'])
def logout():
    if session.get('token'):
        session.pop('token', None)
        return "logged out!"
    else:
        return "You where never logged in!"


# teacher requesting landing page
@app.route('/erequests')
@has_permission('write requests')
def erequests():
    return 'Teacher , Educator Requests'


# generating and printing requests
@app.route('/generaterequests', methods=['GET','POST'])
@has_permission('gen requests')
def printrequests():

    return 'Generating and Printing Page'


# for the attendance office to read what happened. might also send email
@app.route('/attendancereport', methods=['GET'])
@has_permission('read reports')
def attendancereport():

    return 'attendace reports for tina in the office!'


# homepage for all setup related tasks. user might have access to one, but not all
@app.route('/config', methods=['GET', 'POST'])
@has_permission('config')
def config():

    return render_template('config.html')
# page with links to other setup routes
@app.route('/config/dbsetup', methods=['GET', 'POST'])
@has_permission('config')
def dbsetup():
    return render_template('dbsetup.html')


# uploading the users table
@app.route('/config/dbsetup/uploadusers', methods=['GET', 'POST'])
@has_permission('config')
def dbupload_users():
    if request.method == 'POST':
      f = request.files['file']
      return 'uploaded!.'


# uploading the schedule table
@app.route('/config/dbsetup/uploadschedule', methods=['GET', 'POST'])
@has_permission('config')
def dbupload_schedule():
    if request.method == 'POST':
        try: # running try except in case no backup has ever made (first ever run)
            cursor.execute("DROP TABLE schedule_backup") # deletes existing backup table
        except:
            print("No existing backuptable to delete")
        cursor.execute("CREATE TABLE schedule_backup AS SELECT * FROM masterschedule;") # creates new backup table from old schedule
        cursor.execute("DROP TABLE masterschedule;") # deletes old master
        cursor.execute( # creates new table
                        '''CREATE TABLE IF NOT EXISTS masterschedule (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        studentId INT NOT NULL,
                        lastName VARCHAR(25) NOT NULL,
                        firstName VARCHAR(25) NOT NULL,
                        advisoryRoom SMALLINT NOT NULL,
                        period1 SMALLINT,
                        period2 SMALLINT,
                        period4 SMALLINT,
                        period5 SMALLINT,
                        period6 SMALLINT,
                        period7 SMALLINT,
                        period8 SMALLINT
                        );\
                        ''')
        
        csv_file = request.files['file'] # gets file from upload
        csv_data = csv_file.stream.read().decode("utf-8") 
        csv_data = StringIO(csv_data) # Convert the FileStorage object to a text mode file-like object
        csv_reader = csv.reader(csv_data)
        try:
            next(csv_reader)
        except StopIteration: # Handle the case when there are no more rows to iterate over
            pass
        for row in csv_reader: # iterates through and adds following rows
            cursor.execute('''INSERT INTO masterschedule (
                        studentId,
                        lastName,
                        firstName,
                        advisoryRoom,
                        period1,
                        period2,
                        period4,
                        period5,
                        period6,
                        period7,
                        period8)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', row[:11]) # Use row[:11] to exclude the extra value

        # Commit the changes and close the connection
        ## connect.commit()
        return 'uploaded!.'
    

    else:
        return 'Error Somewhere I havent found' # if somehow its a get request instead of POST

# shows current master scedule in a html table
@app.route('/config/dbsetup/currentschedule')
@has_permission('config')
def dbcurrent_schedule():
    cursor.execute("SELECT * FROM masterschedule") # sets schedule to the db 
    rows = cursor.fetchall()
    return render_template('currentschedule.html', rows=rows)


if __name__ == '__main__':
    app.run()
