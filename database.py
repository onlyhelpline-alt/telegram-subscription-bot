import sqlite3
from datetime import datetime

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER,
        username TEXT,
        name TEXT,
        plan_name TEXT,
        join_date TEXT,
        expiry_date TEXT,
        purchase_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mentor TEXT,
        price INTEGER,
        validity INTEGER,
        demo_link TEXT,
        channel_id TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        plan_name TEXT,
        amount INTEGER,
        date TEXT
    )
    """)

    conn.commit()


# 🔹 PLAN FUNCTIONS
def add_plan(name, mentor, price, validity, demo, channel):
    cursor.execute(
        "INSERT INTO plans (name, mentor, price, validity, demo_link, channel_id) VALUES (?, ?, ?, ?, ?, ?)",
        (name, mentor, price, validity, demo, channel),
    )
    conn.commit()


def get_plans():
    cursor.execute("SELECT * FROM plans WHERE active=1")
    return cursor.fetchall()


def delete_plan(plan_id):
    cursor.execute("UPDATE plans SET active=0 WHERE id=?", (plan_id,))
    conn.commit()


# 🔹 USER FUNCTIONS
def add_user(user_id, username, name, plan, join, expiry, purchase):
    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, username, name, plan, join, expiry, purchase),
    )
    conn.commit()


def remove_user(user_id):
    cursor.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()


def get_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


# 🔹 PAYMENT
def add_payment(user_id, plan, amount):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO payments (user_id, plan_name, amount, date) VALUES (?, ?, ?, ?)",
        (user_id, plan, amount, date),
    )
    conn.commit()


def total_revenue():
    cursor.execute("SELECT SUM(amount) FROM payments")
    return cursor.fetchone()[0]


def plan_wise():
    cursor.execute("SELECT plan_name, SUM(amount) FROM payments GROUP BY plan_name")
    return cursor.fetchall()


def daily_sales():
    cursor.execute("SELECT date, SUM(amount) FROM payments GROUP BY date")
    return cursor.fetchall()
