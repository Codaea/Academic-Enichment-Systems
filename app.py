from flask import Flask, request, jsonify, make_response, render_template, session, redirect, url_for
import sqlite3 # databasing software
from functools import wraps # decorators
import jwt # auth
from datetime import datetime, timedelta # sets jwt expiry
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# SQLite database connection
conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# User roles and their corresponding permissions
ROLES = {
    'root': ['read requests', 'write requests', 'gen requests', 'gen reports', 'edit student db', 'edit config'],
    'admin': ['read requests', 'write requests', 'gen requests', 'gen reports', 'edit student db', 'edit config'],
    'eUser': ['read requests', 'write requests', 'gen requests', 'gen reports', 'read reports'],
    'attendance': ['read reports', 'gen reports'],
    'user': ['read requests', 'write requests']
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
        'exp': datetime.utcnow() + timedelta(minutes=5)  # Experation Time Set here (Make a varible later?)
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

# app routes

#home route
@app.route('/', methods=['GET'])
def home():
    token = session.get('token') 
    if token: # checks to see if there even is a token
       if decode_jwt(token=token): # checks for any jwt errors. if any, it returns none from
           #put any code that you want to run when verifyed here on homepage

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
                return response
                
        else:
            error_message = "Invalid credentials. Please try again."

        return render_template('login.html', error_message=error_message)
    else:
        # Render the login page
        return render_template('login.html', error_message='')

# Logout Route. Removes jwt sessiondata
@app.route('/logout', methods=['GET','POST'])
def logout():
    if session.get('token'):
        session.pop('token', None)
        return "logged out!"
    else:
        return "You where never logged in!"

# teacher requesting landing page
@app.route('/erequests', methods=['GET'])
@has_permission('write requests')
def erequests():
    return 'Teacher , Educator Requests'

# generating and printing requests
@app.route('/generaterequests', methods=['GET'])
@has_permission('gen requests')
def printrequests():

    return 'Generating and Printing Page'

# for the attendance office to read what happened. might also send email
@app.route('/attendancereport', methods=['GET'])
@has_permission('read reports')
def attendancereport():

    return 'attendace reports for tina in the office!'

# admin panel, controlls all the student scedules, teacher admins
@app.route('/admin', methods=['GET', 'POST'])
@has_permission('edit student db')
def admin():
    return 'Admin Panel'
    
    # appears to be broken chatgpt code. fix later
    if request.method == 'POST':
        file = request.files['csv_file']
        if file.filename == '':
            return 'No file selected!'
        if file:
            df = pd.read_csv(file)
            connect = sqlite3.connect('database.db')
            df.to_sql('masterschedule', connect, if_exists='replace', index=False)
            conn.close()
            return 'CSV file uploaded and saved to database!'
    return render_template('upload.html')
    


if __name__ == '__main__':
    app.run()
