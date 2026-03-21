import psycopg2
from datetime import datetime
from config import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT,
        username TEXT,
        plan TEXT,
        price INT,
        join_date TEXT,
        expiry_date TEXT
    )
    """)
    conn.commit()


def add_user(uid, username, plan, price, join, expiry):
    cursor.execute(
        "INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s)",
        (uid, username, plan, price, join, expiry)
    )
    conn.commit()


def remove_user(uid):
    cursor.execute("DELETE FROM users WHERE user_id=%s", (uid,))
    conn.commit()


def get_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
