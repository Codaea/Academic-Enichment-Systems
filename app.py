from flask import Flask, request, jsonify, make_response, request, render_template, session, flash
import jwt # used for authentication
from datetime import datetime, timedelta # also used for authentication
from functools import wraps # not sure what this does

app = Flask(__name__)
app.config['SECRET_KEY'] = "b'&x85GFxabx06?xebx0fx96xabxe8xdbxe9x92xb38Lxfbxd7xfbxeaxc8["


def token_required(func): # sets up token authentication
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request/args.get('token')
        if not token:
            return jsonify({'Alert!' : 'Token is missing!'})
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'Alert!' : 'Invalid Token!'})
    return decorated



# Homepage and index
@app.route('/') 
def home():
    if not session.get('logged in'):
        return render_template('login.html')
    else:
        return 'Logged in currently'


# Login route
@app.route('/login', methods=['POST']) 
def login():
    if request.form['username'] and request.form['password'] == 'admin': # Needs to change when adding sql support
        session['logged_in'] = True 
        token = jwt.encode({ # When logged in creats a jwt token
            'user':request.form['username'],
            'expiration': str(datetime.utcnow() + timedelta(seconds=120)) # change for session expiry time
        },
        app.config['SECRET_KEY'])
        return 'logged in!'
    else: 
        return make_response('Unable to verify', 403, {'WWW-Authenticate': 'Basic realm: "Authentication Failed "'}) # if name and password doesnt match with sql/ request form Debug

@app.route('/public')
def public():
    return 'for public'


@app.route('/auth')
@token_required # requires user to be logged in using token required function
def auth():
    return 'JWT token is Verifyed, welcome to dashboard!'




@app.route('/logout', methods=['GET', 'POST']) # Logout Page NOT SETUP
def logout():
    return 'log out DEBUG'

@app.route('/admin', methods=['GET', 'POST']) # admin panel. just cwells or jessie too?
def admin():

    return render_template('admin.html')




if __name__ == '__main__':
    app.run(debug=True) # Debug stuff yk how it is