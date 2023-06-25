    token = session.get('token') # gets token 

    username = decode_jwt(token=token).get('username') # decodes token and gets username

    query = "SELECT * FROM users WHERE username = ?" # prevents sql injection according to chatgpt
    cursor.execute(query, (username,)) # finds username in userdb for templates

    
    
    row = cursor.fetchone() # fetches query results and makes into object userinfo
    advisory_room = row[5]
    teacher_first_name = row[5]
    teacher_last_name = row[4]

    

    if row:
        # put data you want from the row here (SUBTRACT ONE WE START AT 0)
        

        # start of mega hell cause i cant loop and create new var names
        #student_first_name = row[2]
        #student_last_name = row[1]
        #student_id = row[0]
        # all of these fetch periods. need to clean up at some point
        try:
            query = "SELECT * FROM masterschedule WHERE period1 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            
            # need to find a way to inpl
            period1 = cursor.fetchall()
            query = "SELECT * FROM requests WHERE id = ?"
        except:
            print("No Period!")
        
        """
        # commented out atm for just clarity.
        #gonna see if there is a better way to get periods together.
        
        
        try:
            query = "SELECT * FROM masterschedule WHERE period2 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            period2 = cursor.fetchall()
        except:
            print("No Period!")
        try:
            query = "SELECT * FROM masterschedule WHERE period3 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            period3 = cursor.fetchall()
        except:
            print("No Period!")
        try:
            query = "SELECT * FROM masterschedule WHERE period4 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            period4 = cursor.fetchall()
        except:
            print("No Period!")
        try:
            query = "SELECT * FROM masterschedule WHERE period5 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            period5 = cursor.fetchall()
        except:
            print("No Period!")
        try:
            query = "SELECT * FROM masterschedule WHERE period6 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            period6 = cursor.fetchall()
        except:
            print("No Period!")
        try:
            query = "SELECT * FROM masterschedule WHERE period7 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            period7 = cursor.fetchall()
        except:
            print("No Period!")
        try:
            query = "SELECT * FROM masterschedule WHERE period8 = ?"
            cursor.execute(query, (advisory_room,)) # would need to change if we shift away from one room link
            period8 = cursor.fetchall()
        except:
            print("No Period!")


        period2=period2, period3=period3, period4=period4, period5=period5, period6=period6, period7=period7, period8=period8

        """