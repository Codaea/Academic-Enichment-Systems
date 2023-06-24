def login():
    """
    Authenticates the user and returns a JWT token.
    """
    username = request.json.get('username')
    password = request.json.get('password')

    role = authenticate(username, password)
    if role:
        token = create_jwt(username, role)
        return jsonify({'token': token.decode('utf-8')})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401
