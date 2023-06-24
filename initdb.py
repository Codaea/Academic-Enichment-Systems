import os
import sqlite3








# move this to another init file???
if not os.path.exists('database.db'):
    

  # Example using SQLite:
  print("No Database. Creating Now.")
  connect = sqlite3.connect('database.db')
  print("Connected To Database")

  connect.execute( # Creates user db if it doesnt exist
      "CREATE TABLE IF NOT EXISTS users (\
      id INTEGER PRIMARY KEY AUTOINCREMENT,\
      last_name VARCHAR(25) NOT NULL,\
      first_name VARCHAR(25),\
      user_email VARCHAR(200) UNIQUE,\
      password VARCHAR(50),\
      prefix VARCHAR(50),\
      auth_level INTEGER\
    );"
    )
    
  print("Created user database!")

  connect.execute( # creates scheduling database if not created
   "CREATE TABLE IF NOT EXISTS masterschedule (\
    id INTEGER PRIMARY KEY AUTOINCREMENT,\
    studentId INT NOT NULL,\
    lastName VARCHAR(25) NOT NULL,\
    firstName VARCHAR(25) NOT NULL,\
    advisoryRoom SMALLINT NOT NULL,\
    period1 SMALLINT,\
    period2 SMALLINT,\
    period4 SMALLINT,\
    period5 SMALLINT,\
    period6 SMALLINT,\
    period7 SMALLINT,\
    period8 SMALLINT,\
    requested BOOL\
    );"
    );
  print("Created master schedule key!")

  connect.close()

  print("Database created successfully!")
else:
    print("Database already exists.")