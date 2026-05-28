-- Run this FIRST in Azure SQL Query Editor
CREATE TABLE users (
    id       INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(50)  NOT NULL UNIQUE,
    password NVARCHAR(255) NOT NULL
);

INSERT INTO users (username, password) VALUES ('admin', 'pass');
