import sqlite3
from functools import wraps
from flask import Flask, request, jsonify, make_response, render_template
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# SQLite database connection
conn = sqlite3.connect('database.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# User roles and their corresponding permissions
ROLES = {
    'root': ['read requests', 'write requests', 'gen requests', 'gen reports', 'edit db', 'edit config'],
    'admin': ['read requests', 'write requests', 'gen requests', 'gen reports', 'edit db', 'edit config'],
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
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=2) #change for login expiry time
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
        return None


def has_permission(permission):
    """
    Decorator function to check if the user has the required permission.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get('Authorization')
            if token:
                token = token.split('Bearer ')[1]
                payload = decode_jwt(token)
                if payload and 'role' in payload:
                    role = payload['role']
                    if permission in ROLES.get(role, []):
                        return f(*args, **kwargs)
            return jsonify({'message': 'Unauthorized'}), 401
        return wrapper
    return decorator

# app routes

@app.route('/', methods=['GET'])
def home():
    print('hmpage called')
    return 'Home page'
# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders the login page and authenticates the user.
    """
    if request.method == 'POST':
        # Handle form submission
        username = request.form.get('username')
        password = request.form.get('password')

        # Authentication logic
        if authenticate(username, password):
            # User authenticated successfully, perform further actions
            return "User authenticated successfully!"
        else:
            error_message = "Invalid credentials. Please try again."

        return render_template('login.html', error_message=error_message)
    else:
        # Render the login page
        return render_template('login.html', error_message='')

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
def admin():
    
    return 'Admin Panel'


if __name__ == '__main__':
    app.run()
