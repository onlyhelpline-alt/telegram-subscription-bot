import psycopg2
from datetime import datetime
from config import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id SERIAL PRIMARY KEY,
        name TEXT,
        mentor TEXT,
        price INT,
        validity INT,
        demo_link TEXT,
        channel_id TEXT,
        active INT DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT,
        username TEXT,
        name TEXT,
        plan_id INT,
        join_date TEXT,
        expiry_date TEXT,
        purchase_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        plan_id INT,
        amount INT,
        date TEXT
    )
    """)

    conn.commit()


def add_plan(name, mentor, price, validity, demo, channel):
    cursor.execute(
        "INSERT INTO plans (name, mentor, price, validity, demo_link, channel_id) VALUES (%s,%s,%s,%s,%s,%s)",
        (name, mentor, price, validity, demo, channel)
    )
    conn.commit()

def get_plans():
    cursor.execute("SELECT * FROM plans WHERE active=1")
    return cursor.fetchall()

def get_plan(pid):
    cursor.execute("SELECT * FROM plans WHERE id=%s", (pid,))
    return cursor.fetchone()

def delete_plan(pid):
    cursor.execute("UPDATE plans SET active=0 WHERE id=%s", (pid,))
    conn.commit()


def add_user(uid, username, name, pid, join, expiry, purchase):
    cursor.execute(
        "INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (uid, username, name, pid, join, expiry, purchase)
    )
    conn.commit()

def remove_user(uid):
    cursor.execute("DELETE FROM users WHERE user_id=%s", (uid,))
    conn.commit()

def get_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


def add_payment(uid, pid, amount):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO payments (user_id, plan_id, amount, date) VALUES (%s,%s,%s,%s)",
        (uid, pid, amount, date)
    )
    conn.commit()

def total_revenue():
    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payments")
    return cursor.fetchone()[0]
