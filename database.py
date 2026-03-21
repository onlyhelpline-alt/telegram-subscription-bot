import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")

# ================= CONNECTION =================
def get_conn():
    return psycopg2.connect(DATABASE_URL)


# ================= INIT =================
def init_db():
    conn = get_conn()
    cur = conn.cursor()

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
    cur.close()
    conn.close()


# ================= USERS =================
def add_user(uid, username, plan, price, join, exp):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users VALUES (%s,%s,%s,%s,%s,%s)",
        (uid, username, plan, price, join, exp)
    )

    conn.commit()
    cur.close()
    conn.close()


def get_users():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    data = cur.fetchall()

    cur.close()
    conn.close()
    return data


def remove_user(uid):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE user_id=%s", (uid,))

    conn.commit()
    cur.close()
    conn.close()


# ================= PLANS =================
def add_plan(key, name, price, days, demo, channel):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO plans (plan_key, name, price, validity, demo_link, channel_id)
    VALUES (%s,%s,%s,%s,%s,%s)
    ON CONFLICT (plan_key)
    DO UPDATE SET
        name = EXCLUDED.name,
        price = EXCLUDED.price,
        validity = EXCLUDED.validity,
        demo_link = EXCLUDED.demo_link,
        channel_id = EXCLUDED.channel_id
    """, (key, name, price, days, demo, channel))

    conn.commit()
    cur.close()
    conn.close()


def get_plans():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM plans")
    data = cur.fetchall()

    cur.close()
    conn.close()
    return data


def get_plan(key):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM plans WHERE plan_key=%s", (key,))
    data = cur.fetchone()

    cur.close()
    conn.close()
    return data


def delete_plan(key):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM plans WHERE plan_key=%s", (key,))

    conn.commit()
    cur.close()
    conn.close()
