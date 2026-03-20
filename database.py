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


# ================= PLAN =================
def add_plan(name, mentor, price, validity, demo, channel):
    cursor.execute(
        "INSERT INTO plans (name, mentor, price, validity, demo_link, channel_id) VALUES (%s,%s,%s,%s,%s,%s)",
        (name, mentor, price, validity, demo, channel)
    )
    conn.commit()

def get_plans():
    cursor.execute("SELECT * FROM plans WHERE active=1")
    return cursor.fetchall()

def get_plan(plan_id):
    cursor.execute("SELECT * FROM plans WHERE id=%s", (plan_id,))
    return cursor.fetchone()

def delete_plan(plan_id):
    cursor.execute("UPDATE plans SET active=0 WHERE id=%s", (plan_id,))
    conn.commit()

def update_plan(plan_id, field, value):
    cursor.execute(f"UPDATE plans SET {field}=%s WHERE id=%s", (value, plan_id))
    conn.commit()


# ================= USER =================
def add_user(user_id, username, name, plan_id, join, expiry, purchase):
    cursor.execute(
        "INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (user_id, username, name, plan_id, join, expiry, purchase)
    )
    conn.commit()

def remove_user(user_id):
    cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


# ================= PAYMENT =================
def add_payment(user_id, plan_id, amount):
    date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "INSERT INTO payments (user_id, plan_id, amount, date) VALUES (%s,%s,%s,%s)",
        (user_id, plan_id, amount, date)
    )
    conn.commit()

def total_revenue():
    cursor.execute("SELECT COALESCE(SUM(amount),0) FROM payments")
    return cursor.fetchone()[0]

def plan_wise():
    cursor.execute("""
    SELECT plans.name, SUM(payments.amount)
    FROM payments
    JOIN plans ON payments.plan_id = plans.id
    GROUP BY plans.name
    """)
    return cursor.fetchall()

def daily_sales():
    cursor.execute("SELECT date, SUM(amount) FROM payments GROUP BY date")
    return cursor.fetchall()
