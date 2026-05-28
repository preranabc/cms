import pyodbc
import sqlite3
from flask import current_app


def get_connection():
    if current_app.config['DATABASE_BACKEND'] == 'sqlite':
        conn = sqlite3.connect(current_app.config['SQLITE_DATABASE'])
        conn.row_factory = sqlite3.Row
        return conn

    conn_str = (
        f"DRIVER={{{current_app.config['SQL_DRIVER']}}};"
        f"SERVER=tcp:{current_app.config['SQL_SERVER']},1433;"
        f"DATABASE={current_app.config['SQL_DATABASE']};"
        f"UID={current_app.config['SQL_USER_NAME']};"
        f"PWD={current_app.config['SQL_PASSWORD']};"
        "Encrypt=yes;"
        f"TrustServerCertificate={current_app.config['SQL_TRUST_SERVER_CERTIFICATE']};"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)


def init_db():
    if current_app.config['DATABASE_BACKEND'] != 'sqlite':
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            image_url TEXT
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
        ('admin', 'pass')
    )
    conn.commit()
    conn.close()


def get_all_articles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, body, image_url FROM articles ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_article(article_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, author, body, image_url FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def insert_article(title, author, body, image_url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO articles (title, author, body, image_url) VALUES (?, ?, ?, ?)",
        (title, author, body, image_url)
    )
    conn.commit()
    conn.close()


def update_article(article_id, title, author, body, image_url):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE articles SET title=?, author=?, body=?, image_url=? WHERE id=?",
        (title, author, body, image_url, article_id)
    )
    conn.commit()
    conn.close()


def delete_article(article_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM articles WHERE id=?", (article_id,))
    conn.commit()
    conn.close()


def get_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username FROM users WHERE username=? AND password=?",
        (username, password)
    )
    row = cursor.fetchone()
    conn.close()
    return row
