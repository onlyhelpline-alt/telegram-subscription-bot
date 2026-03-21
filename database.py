import psycopg2
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id SERIAL PRIMARY KEY,
        name TEXT,
        price INT,
        validity INT
    )
    """)

    conn.commit()


# ---------- USERS ----------
def add_user(uid, username, plan, price, join, expiry):
    cursor.execute(
        "INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s)",
        (uid, username, plan, price, join, expiry)
    )
    conn.commit()

def get_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

def remove_user(uid):
    cursor.execute("DELETE FROM users WHERE user_id=%s", (uid,))
    conn.commit()


# ---------- PLANS ----------
def add_plan(name, price, validity):
    cursor.execute(
        "INSERT INTO plans (name, price, validity) VALUES (%s,%s,%s)",
        (name, price, validity)
    )
    conn.commit()

def get_plans():
    cursor.execute("SELECT * FROM plans")
    return cursor.fetchall()
