import os
import asyncio
import sqlite3
import random
import string
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

ADMIN_USERNAME = "@ckg2754"

# DATABASE
conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
expiry TEXT
)
""")
conn.commit()


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    code = generate_code()

    text = f"""
🔥 VIP Subscription Access

1️⃣ Payment करो (UPI / QR)

2️⃣ Screenshot लो

3️⃣ Payment proof और code इस ID पर भेजो

👉 {ADMIN_USERNAME}

📌 Payment Code: {code}

Payment के बाद message भेजो।
"""

    await update.message.reply_text(text)


# ADD USER
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        user_id = int(context.args[0])
        days = int(context.args[1])

        expiry = datetime.now() + timedelta(days=days)

        cur.execute(
            "INSERT OR REPLACE INTO users VALUES (?,?)",
            (user_id, expiry.strftime("%Y-%m-%d"))
        )

        conn.commit()

        await context.bot.unban_chat_member(GROUP_ID, user_id)

        await context.bot.send_message(
            user_id,
            f"✅ Subscription Activated\n\nExpiry Date: {expiry.date()}"
        )

        await update.message.reply_text("User Added Successfully")

    except:

        await update.message.reply_text("Usage:\n/add USER_ID DAYS")


# REMOVE USER
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        user_id = int(context.args[0])

        cur.execute("DELETE FROM users WHERE user_id=?", (user_id,))
        conn.commit()

        await context.bot.ban_chat_member(GROUP_ID, user_id)

        await update.message.reply_text("User Removed")

    except:

        await update.message.reply_text("Usage:\n/remove USER_ID")


# LIST USERS
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT * FROM users")

    data = cur.fetchall()

    text = "Active Users:\n\n"

    for u in data:

        text += f"{u[0]} | Expiry: {u[1]}\n"

    await update.message.reply_text(text)


# CHECK EXPIRY
async def check_expiry(context: ContextTypes.DEFAULT_TYPE):

    now = datetime.now()

    cur.execute("SELECT * FROM users")

    users = cur.fetchall()

    for user in users:

        user_id = user[0]
        expiry = datetime.strptime(user[1], "%Y-%m-%d")

        if expiry < now:

            await context.bot.ban_chat_member(GROUP_ID, user_id)

            cur.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit()

        elif expiry - now <= timedelta(days=1):

            await context.bot.send_message(
                user_id,
                f"⚠️ Subscription Expiring Soon\n\nRenew now.\n\nContact {ADMIN_USERNAME}"
            )


# MAIN
async def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("users", users))

    job = app.job_queue
    job.run_repeating(check_expiry, interval=3600)

    print("Bot Started")

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
