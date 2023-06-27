from flask import Flask, request, jsonify, make_response, render_template, session, redirect, url_for
import sqlite3 # databasing software
from functools import wraps # decorators
import jwt # auth
from datetime import datetime, timedelta # sets jwt expiry
import json # auth checking
import csv # for db uploading
from io import StringIO # done for csv conversion to sqlite
import time # for waiting before rerouting
import pdfkit # for making pdfs from html

app = Flask(__name__)


app.config['SECRET_KEY'] = 'your-secret-key' # make something secure, ive been using this for a while now
#https://wkhtmltopdf.org/index.html
pdfkit_config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe') # /path/to/wkhtmltopdf 




# SQLite database connection
connect = sqlite3.connect('database.db', check_same_thread=False)
connect.row_factory = sqlite3.Row
cursor = connect.cursor()



# User roles and their corresponding permissions
ROLES = {
    'root': ['read requests', 'write requests', 'gen requests', 'reports', 'config'],
    'admin': ['read requests', 'write requests', 'gen requests', 'reports','edit schedule'],
    'eUser': ['read requests', 'write requests', 'gen requests', 'reports'],
    'attendance': ['reports'],
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
        SELECT requests.requested_room
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
        print(period)

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

            cursor.execute("INSERT INTO requests (studentId, requested_room) VALUES (?, ?)", (student_id, requesting_room,))

        # commit changes and close
        connect.commit()
        return 'success!'


# admin control interface for Cwells
@app.route('/apanel')
@has_permission('gen requests')
def admin_panel():

    # put a button on here that manages request dbs
    return render_template('apanel.html')


# generating and printing requests
@app.route('/apanel/generaterequestspdf', methods=['GET','POST'])
@has_permission('gen requests')
def printrequests():
    
    # cleanup (commented out for tests) 
    
    cursor.execute("SELECT id FROM genrequests")  # sees if table exists
    result = cursor.fetchone
    if result: # does cleanup on old tables and backs it up to lastgenrequests 
        cursor.execute("CREATE TABLE lastgenrequests AS SELECT * FROM genrequests;") # backs up table if it exists
        cursor.execute("DROP TABLE genrequests") # deletes it 

        
    else: pass # incase its the first ever run
    
    query = '''
    CREATE TABLE genrequests (
    id INTEGER PRIMARY KEY,
    studentID INT,
    requested_room TEXT,
    advisory_room TEXT,
    firstName TEXT,
    lastName TEXT,
    prefix TEXT,
    last_name TEXT
    );

    INSERT INTO genrequests (studentID, requested_room, advisory_room, firstName, lastName, prefix, last_name)
    SELECT r.studentID, r.requested_room, u.advisory_room, m.firstName, m.lastName, u.prefix, u.last_name
    FROM requests r
    JOIN masterschedule m ON r.studentID = m.studentID
    JOIN users u ON r.requested_room = u.advisory_room;
    ''' # creates table and inserts new data into it

    cursor.execute(query) # creates genrequest table 

    # Drops old requests table and makes a new one 
    
    try:# drops  requests and makes new requests tables for next iteration
        cursor.execute("DROP TABLE requests") 
        cursor.execute('''
        CREATE TABLE  requests (
        studentId INTEGER NOT NULL,
        requested_room VARCHAR
        );''')
        
    except: pass

    # main part

    query = '''
    SELECT *
    FROM genrequests
    ORDER BY advisory_room ASC,
    lastName DESC;
        
    ''' 

    cursor.execute(query) # selection for html template input

    rows = cursor.fetchall() # gets selection to pass into render_template
    # [row[column]]
    # columns start at 0. id, StudentID, requestedroom, advisoryroom, firstName, lastName, prefix, teachername
    print(rows)


    rendered = render_template('requestspdftemplate.html', rows=rows)
    try:
    # Generate the PDF from the HTML content
        pdf = pdfkit.from_string(rendered, False, configuration=pdfkit_config)

    except IOError as e: # clean this up future me
        print("wkhtmltopdf reported an error:")
        print(e)

    # Return the PDF as a response
    response = app.make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=Requests.pdf'
    return response



    

    #run this stuff at the end, after all as a cleanup step

    
    
    
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
    app.run(debug=True)
