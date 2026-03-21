import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


def init_db():
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT,
        username TEXT,
        plan TEXT,
        price INT,
        join_date TEXT,
        expiry TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS plans (
        plan_key TEXT PRIMARY KEY,
        name TEXT,
        price INT,
        validity INT,
        demo_link TEXT,
        channel_id BIGINT
    )
    """)
    conn.commit()


# ================= USERS =================
def add_user(uid, username, plan, price, join, exp):
    cur.execute("INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s)",
                (uid, username, plan, price, join, exp))
    conn.commit()


def get_users():
    cur.execute("SELECT * FROM users")
    return cur.fetchall()


def remove_user(uid):
    cur.execute("DELETE FROM users WHERE user_id=%s", (uid,))
    conn.commit()


# ================= PLANS =================
def add_plan(key, name, price, days, demo, channel):
    cur.execute(
        "INSERT INTO plans VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (plan_key) DO UPDATE SET name=%s,price=%s,validity=%s,demo_link=%s,channel_id=%s",
        (key, name, price, days, demo, channel,
         name, price, days, demo, channel)
    )
    conn.commit()


def get_plans():
    cur.execute("SELECT * FROM plans")
    return cur.fetchall()


def get_plan(key):
    cur.execute("SELECT * FROM plans WHERE plan_key=%s", (key,))
    return cur.fetchone()


def delete_plan(key):
    cur.execute("DELETE FROM plans WHERE plan_key=%s", (key,))
    conn.commit()
