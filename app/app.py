from flask import Flask, request, jsonify, make_response, render_template, session, redirect, url_for, send_file
import sqlite3 # databasing software
from functools import wraps # decorators
import jwt # auth
from datetime import datetime, timedelta # sets jwt expiry
import json # auth checking
import csv # for db uploading
from io import StringIO, BytesIO # done for csv conversion to sqlite, and qr code to base64
import time # for waiting before rerouting (unused atm)
import qrcode # for scanning pages
import base64 # directly passing in images to html (for qr codes)
from PIL import Image # proccessing pdf uploads
from pdf2image import convert_from_bytes # pdf to image


app = Flask(__name__)


app.config['SECRET_KEY'] = 'your-secret-key' # make something secure, ive been using this for a while now



# SQLite database connection
connect = sqlite3.connect('database.db', check_same_thread=False)
connect.row_factory = sqlite3.Row
cursor = connect.cursor()



# User roles and their corresponding permissions
ROLES = {
    'root': ['read requests', 'write requests', 'gen requests', 'reports', 'config', 'edit schedule'],
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

# ran before app
def setup():
    print('running setup!')

    # users table setup
    try:
        cursor.execute('''
        CREATE TABLE users (
        id INTEGER,
        username VARCHAR,
        password VARCHAR,
        last_name VARCHAR,
        first_name VARCHAR,
        advisory_room SMALLINT,
        user_email VARCHAR,
        prefix VARCHAR,
        role VARCHAR
    );''') # creates usertable if it doesnt exist
        cursor.execute('''
        INSERT INTO users (
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
    VALUES (1, 'root', 'root', 'root', 'root', 999, 'root@gmail.com', 'Mr.', 'root');
    ''') # adds setup user with name root and root
    except:
        print('users table already made!')
    
    # requests table setup
    try:
        cursor.execute('''
        CREATE TABLE  requests (
        studentId INTEGER NOT NULL,
        requested_room VARCHAR,
        priority INT
        );''')
    except: print('requests table already exists!')


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
                return redirect('/apanel')
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


# handles erequest form and adds to requests table in db from /erequests
@app.route('/processerequests', methods=['GET','POST'])
@has_permission('requests')
def proccess_erequests():
    if request.method == 'POST':
        # form proccessing logic here

        lowSelectedIds = request.form.getlist('low_selected_rows[]')
        mediumSelectedIds = request.form.getlist('medium_selected_rows[]')
        highSelectedIds = request.form.getlist('high_selected_rows[]')


        requesting_room = request.form.get('requesting_room')

        for lowSelectedId in lowSelectedIds:
            priority = 1
            cursor.execute("INSERT INTO requests (studentId, requested_room, priority) VALUES (?, ?, ?)", (lowSelectedId, requesting_room, priority,))

        for mediumSelectedId in mediumSelectedIds:
            priority = 2
            cursor.execute("INSERT INTO requests (studentId, requested_room, priority) VALUES (?, ?, ?)", (mediumSelectedId, requesting_room, priority,))

        for highSelectedId in highSelectedIds:
            priority = 3
            cursor.execute("INSERT INTO requests (studentId, requested_room, priority) VALUES (?, ?, ?)", (highSelectedId, requesting_room, priority,))



        # commit changes and close
        connect.commit()
        return 'success!'


# admin control interface for Cwells
@app.route('/apanel')
@has_permission('gen requests')
def admin_panel():

    # put a button on here that manages request dbs
    return render_template('apanel/apanel.html')


# makes a are you sure about uploading requests just in case
@app.route('/apanel/generaterequestsareyousure')
def genrequests_check():
    return render_template('apanel/generaterequestspdfareyousure.html')


# generating and printing requests
@app.route('/apanel/generaterequestspdf', methods=['GET','POST'])
@has_permission('gen requests')
def printrequests():
    
    # precleaning

    # for first run incase no table
    try:
        cursor.execute("DROP TABLE IF EXISTS genrequests") # deletes genrequest for new iteration if it exists
    except:
        print('No genrequests table to drop! making new table..')
    finally: # makes new genrequests table
        query = '''
        CREATE TABLE genrequests (
        id INTEGER PRIMARY KEY,
        studentID INT,
        requested_room TEXT,
        advisory_room TEXT,
        firstName TEXT,
        lastName TEXT,
        prefix TEXT,
        last_name TEXT,
        base64qr BLOB,
        priority INT
        );'''
        
        cursor.execute(query) # creates genrequest table 
        print('New Table!')

    query = '''
    INSERT INTO genrequests (studentID, requested_room, advisory_room, firstName, lastName, prefix, last_name, priority)
    SELECT r.studentID, r.requested_room, u.advisory_room, m.firstName, m.lastName, u.prefix, u.last_name, r.priority
    FROM requests r
    JOIN masterschedule m ON r.studentID = m.studentID
    JOIN users u ON r.requested_room = u.advisory_room;
    ''' # creates table and inserts new data into it

    cursor.execute(query) # Inserts all normal values in genrequests
    
    # QR code generation

    cursor.execute("SELECT * FROM genrequests")

    rows = cursor.fetchall()

    for row in rows: # makes qr code per row
        id_value = row[0] # id row here
        
        # creating qr code
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
        qr.add_data(str(id_value))
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white") # actually makes the qr code and assigns it to qr_image

        # Convert the qrcode to a base64-encoded string
        byte_stream = BytesIO()
        qr_image.save(byte_stream,) # Converts into bytes
        qr_image_data = byte_stream.getvalue() # gets the conversion

        base64_image = base64.b64encode(qr_image_data).decode('utf-8') # converts bytes to pngstring
        
        #print(base64_image)

        # adds base64string to sql table

        query = "UPDATE genrequests SET base64qr = ? WHERE id = ?"

        cursor.execute(query, (base64_image, id_value))
    
    connect.commit()

    
    try:
        cursor.execute("DROP TABLE requests") 
        cursor.execute('''
        CREATE TABLE  requests (
        studentId INTEGER NOT NULL,
        requested_room VARCHAR,
        priority INT
        );''')
        
    except: pass
    
    # End of Precleaning
    
    # MAIN CODE

    # ordering table before pdf conversion
    query = '''
    SELECT *
    FROM genrequests
    ORDER BY advisory_room ASC,
    lastName DESC;
        
    ''' 

    cursor.execute(query) # selection for html template input

    rows = cursor.fetchall() # gets selection to pass into render_template
    # [row[column]]
    # columns start at 0. id, StudentID, requestedroom, advisoryroom, firstName, lastName, prefix, teachername, qrcodeBase64, priority, 10
    
    
    
    # rendering pdf


    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib import colors

    c = canvas.Canvas("output.pdf", pagesize=A4)
    

    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))

    

    for row in rows:

        # do whatever is needed for this page

        # title draw
        c.setFont('Arial', 30) # increase font size to 30
        c.drawString(105, 800, "Academic Enrichment Request")

        # main body draw

        c.setFont('Arial', 12) 
        c.drawString(50, 750, f"{row[4]} {row[5]}, You Have Been Requested By {row[6]} {row[7]}. Please go to {row[2]}.")
        c.drawString(50, 730, f"Priority Level {row[9]}, Student Id {row[1]}, ")


        c.showPage() # add new page to pdf
    

    c.save() # save pdf

    return send_file('output.pdf') # send pdf to user

        
    



    
  #  response = make_response(pdf_bytes)
  #  response.headers['Content-Type'] = 'application/pdf'
  #  response.headers['Content-Disposition'] = 'attachment; filename=output.pdf'
  #  return response


# help page for cwells
@app.route('/apanel/help')
@has_permission('gen requests')
def apanel_help():
    return render_template('apanel/help.html')


# for the attendance office to read what happened. might also send email
@app.route('/reports', methods=['GET'])
@has_permission('reports')
def attendancereport():

    try:
        cursor.execute("SELECT * FROM Report")
        rows = cursor.fetchall()
    except:
        print('no rows to return for attendace reports!')

    return render_template('reports.html', rows=rows)


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
@has_permission('edit schedule')
def dbupload_schedule():
    if request.method == 'POST':
        try: # running try except in case no backup has ever made (first ever run)
            cursor.execute("DROP TABLE schedule_backup") # deletes existing backup table
        except:
            print("No existing backuptable to delete")
        try:
            cursor.execute("CREATE TABLE schedule_backup AS SELECT * FROM masterschedule;") # creates new backup table from old schedule
        except: print('no masterschedule to backup!')
        
        
        try:
            cursor.execute("DROP TABLE masterschedule;") # deletes old master
        except: print('no master schedule table to delete')
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
        try:
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
        except: 
            return 'Something went wrong. is the scedule format right?'
    

    else:
        return 'Error With Table!' # if somehow its a get request instead of POST

# shows current master scedule in a html table
@app.route('/config/dbsetup/currentschedule')
@has_permission('edit schedule')
def dbcurrent_schedule():
    cursor.execute("SELECT * FROM masterschedule") # sets schedule to the db 
    rows = cursor.fetchall()
    return render_template('config/currentschedule.html', rows=rows)

setup()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
