from flask import Flask, request, jsonify, make_response, render_template, session, redirect, url_for
import sqlite3 # databasing software
from functools import wraps # decorators
import jwt # auth
from datetime import datetime, timedelta # sets jwt expiry
import json # auth checking
import csv # for db uploading
from io import StringIO # done for csv conversion to sqlite
import time # for waiting before rerouting


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
            return redirect('/login')
        return wrapper
    return decorator


#----------------------------#
#       ALL APP ROUTES       #
#----------------------------#

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
                return redirect('erequests')
            elif role == 'attendance':
                return 'attendance'
            elif role == 'admin':
                return 'admin'
            elif role == 'eUser':
                return 'Elivated User'
            elif role == 'root':
                return redirect('/config')
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


# Logout Route. Removes jwt sessiondata. might need to use POST form in future.
@app.route('/logout', methods=['GET','POST'])
def logout():
    if session.get('token'):
        session.pop('token', None)
        
        return redirect('/login')
    else:
        return "You where never logged in!"


# teacher requesting landing page
@app.route('/erequests')
@has_permission('requests')
def erequests():

    token = session.get('token') # gets token 

    username = decode_jwt(token=token).get('username') # decodes token and gets username

    query = "SELECT * FROM users WHERE username = ?" # prevents sql injection according to chatgpt
    cursor.execute(query, (username,)) # finds username in userdb for templates

    
    
    row = cursor.fetchone() # fetches query results and makes into object userinfo
    advisory_room = row[5]
    teacher_first_name = row[5]
    teacher_last_name = row[4]
    
    all_periods = {} # creating a dictonary for all periods
    # all_periods = {periods_# [ all rows [ columns]]}
    for i in range(0,9):
        
        query = f'''
        SELECT masterschedule.*, (
        SELECT requests.requested_rooms
        FROM requests
        WHERE requests.studentId = masterschedule.studentId
        ) AS matched_value
        FROM masterschedule
        WHERE masterschedule.period{i} = ?;
        '''# query increments periods by 1 every run with 'i'

        try: 
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
        except: pass

        period = cursor.fetchall() # assigns [allrows[columns]] to period
        

        all_periods[i] = period # adds new period to dict every loop and sets to current cursor fetch (more lists of lists)
        # all_periods = {periods_# [ all rows [ columns]]}





    return render_template('erequest.html', all_periods=all_periods, Fname=teacher_first_name, Room_Number=advisory_room, )


# handles erequest form and adds to requests table in db
@app.route('/processerequests', methods=['GET','POST'])
@has_permission('requests')
def proccess_erequests():
    if request.method == 'POST':
        # form proccessing logic here

        selected_ids = request.form.getlist('selected_rows[]')
        requesting_room = request.form.get('requesting_room')


        for student_id in selected_ids:


            print(student_id)

            cursor.execute("SELECT * FROM requests WHERE studentId = ?", (student_id,)) # comma required on student_id, so its not treated as a tuple  ¯\_(ツ)_/¯
            existing_row = cursor.fetchone()

            
            if existing_row:
            # Row exists, concatenate the existing requesting room with the new value
                existing_requested_room = existing_row[1]  # Assuming the requesting room is stored in the second column
                new_requesting_room = f"{existing_requested_room}, {requesting_room}"
                cursor.execute("UPDATE requests SET requested_rooms = ? WHERE studentId = ?", (new_requesting_room, student_id,))

            else:
            # Row doesn't exist, insert a new row
                cursor.execute("INSERT INTO requests (studentId, requested_rooms) VALUES (?, ?)", (student_id, requesting_room,))

        # commit changes and close
        connect.commit()
        return 'success!'




# generating and printing requests
@app.route('/generaterequests', methods=['GET','POST'])
@has_permission('gen requests')
def printrequests():














    
    """
    try:
        cursor.execute("DROP TABLE requests") # need to add backing up old tables for attendance desk
        cursor.execute('''
        CREATE TABLE  requests (
        studentId INTEGER PRIMARY KEY NOT NULL,
        requested_rooms VARCHAR
        );''')
        
    except: pass
    """
    # put a button on here that manages request dbs
    return 'Generating and Printing Page'


# for the attendance office to read what happened. might also send email
@app.route('/attendancereport', methods=['GET'])
@has_permission('read reports')
def attendancereport():

    return 'attendace reports for tina in the office!'


#----------------------------#
# CONFIGURATION ROUTES BELOW #
#----------------------------#


# homepage for all setup related tasks. user might have access to one, but not all
@app.route('/config', methods=['GET', 'POST'])
#@has_permission('config')
def config():

    return render_template('config/config.html')


# page with links to other setup routes
@app.route('/config/dbsetup', methods=['GET', 'POST'])
@has_permission('config')
def dbsetup():
    return render_template('config/dbsetup.html')


# uploading the users table
@app.route('/config/dbsetup/uploadusers', methods=['GET', 'POST'])
@has_permission('config')
def dbupload_users():
    if request.method == 'POST':
        try: # running try except in case no backup has ever made (first ever run)
            cursor.execute("DROP TABLE users") # deletes existing users table
        except:
            print("No user Table to drop!")
        cursor.execute( # creates new table
                        '''CREATE TABLE users (
                        id INTEGER,
                        username VARCHAR,
                        password VARCHAR,
                        last_name VARCHAR,
                        first_name VARCHAR,
                        advisory_room SMALLINT,
                        user_email VARCHAR,
                        prefix VARCHAR,
                        role VARCHAR
                        );
                        ''')
        
        csv_file = request.files['file'] # gets file from upload
        print(csv_file) # test1 
        csv_data = csv_file.stream.read().decode("utf-8") 
        csv_data = StringIO(csv_data) # Convert the FileStorage object to a text mode file-like object
        csv_reader = csv.reader(csv_data)
        print(csv_reader)
        try:
            next(csv_reader)
        except StopIteration: # Handle the case when there are no more rows to iterate over
            pass

        for row in csv_reader: # iterates through and adds following rows
            cursor.execute('''INSERT INTO users (
                            id,
                            username,
                            password,
                            last_name, 
                            first_name,
                            advisory_room,
                            user_email,
                            prefix,
                            role
                            )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', row)
        connect.commit()# Commit the changes and close the connection
        return 'uploaded!'
    else:
        return 'wrong request type'


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
                        studentId INTEGER,
                        lastName VARCHAR(25) NOT NULL,
                        firstName VARCHAR(25) NOT NULL,
                        advisoryRoom SMALLINT NOT NULL,
                        period1 SMALLINT,
                        period2 SMALLINT,
                        period3 SMALLINT,
                        period4 SMALLINT,
                        period5 SMALLINT,
                        period6 SMALLINT,
                        period7 SMALLINT,
                        period8 SMALLINT
                        );
                        ''')
        
        csv_file = request.files['file'] # gets file from upload
        csv_data = csv_file.stream.read().decode("utf-8") 
        csv_data = StringIO(csv_data) # Convert the FileStorage object to a text mode file-like object
        csv_reader = csv.reader(csv_data)
        try:
            next(csv_reader)
        except StopIteration: # Handle the case when there are no more rows to iterate over
            pass
        #try:
        for row in csv_reader: # iterates through and adds following rows
            cursor.execute('''INSERT INTO masterschedule (
                        studentId,
                        lastName,
                        firstName,
                        advisoryRoom,
                        period1,
                        period2,
                        period3,
                        period4,
                        period5,
                        period6,
                        period7,
                        period8)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', row)
        connect.commit()# Commit the changes and close the connection
        return 'uploaded!'
    

    else:
        return 'Error With Table!' # if somehow its a get request instead of POST

# shows current master scedule in a html table
@app.route('/config/dbsetup/currentschedule')
@has_permission('config')
def dbcurrent_schedule():
    cursor.execute("SELECT * FROM masterschedule") # sets schedule to the db 
    rows = cursor.fetchall()
    connect.close()
    return render_template('config/currentschedule.html', rows=rows)


if __name__ == '__main__':
    app.run()
