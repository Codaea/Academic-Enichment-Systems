THIS IS ALL OUTDATED, CHECK initdb.py


CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name VARCHAR(25) NOT NULL,
    first_name VARCHAR(25),
    user_email VARCHAR(200) UNIQUE,
    password VARCHAR(50), NOT NULL
    prefix VARCHAR(50),
    room INTEGER NOT NULL
);


CREATE TABLE IF NOT EXISTS masterschedule (
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
    );

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_name VARCHAR(25) NOT NULL,
    first_name VARCHAR(25),
    user_email VARCHAR(200) UNIQUE,
    password VARCHAR(50),
    prefix VARCHAR(50)
);