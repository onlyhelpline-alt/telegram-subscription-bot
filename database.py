import sqlite3

def init_db():
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER,
        username TEXT,
        plan TEXT,
        price INTEGER,
        join_date TEXT,
        expiry TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS plans(
        key TEXT PRIMARY KEY,
        name TEXT,
        price INTEGER,
        validity INTEGER,
        demo TEXT,
        channel INTEGER
    )""")

    conn.commit()
    conn.close()


def add_user(uid, username, plan, price, join, expiry):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO users VALUES (?,?,?,?,?,?)",
                (uid, username, plan, price, join, expiry))
    conn.commit()
    conn.close()


def get_users():
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users")
    data = cur.fetchall()
    conn.close()
    return data


def remove_user(uid):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()


def add_plan_db(key, name, price, days, demo, channel):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO plans VALUES (?,?,?,?,?,?)",
                (key, name, price, days, demo, channel))
    conn.commit()
    conn.close()


def get_plans():
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM plans")
    data = cur.fetchall()
    conn.close()
    return data


def update_plan(key, price, days):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("UPDATE plans SET price=?, validity=? WHERE key=?",
                (price, days, key))
    conn.commit()
    conn.close()


def delete_plan_db(key):
    conn = sqlite3.connect("data.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM plans WHERE key=?", (key,))
    conn.commit()
    conn.close()
