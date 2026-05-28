-- Run this SECOND in Azure SQL Query Editor
CREATE TABLE articles (
    id        INT PRIMARY KEY IDENTITY(1,1),
    title     NVARCHAR(255) NOT NULL,
    author    NVARCHAR(100) NOT NULL,
    body      NVARCHAR(MAX) NOT NULL,
    image_url NVARCHAR(500) NULL
);
