CREATE TABLE IF NOT EXISTS USERS (
    id int NOT NULL AUTO_INCREMENT,
    lastName varchar(255) NOT NULL,
    firstName varchar(255),
    email varchar(255),
    password varchar(255),
    prefix varchar(50),

    );


CREATE TABLE IF NOT EXISTS MASTERSCHEDULE (
    id int NOT NULL AUTO_INCREMENT,
    studentId int NOT NULL,
    lastName varchar(255) NOT NULL,
    firstName varchar(255) NOT NULL,
    advisoryRoom SMALLINT NOT NULL,
    1Period SMALLINT,
    2Period SMALLINT,
    4Period SMALLINT,
    5Period SMALLINT,
    6Period SMALLINT,
    7Period SMALLINT,
    8Period SMALLINT,
);
