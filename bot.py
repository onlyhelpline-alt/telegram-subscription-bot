import os
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

conn = sqlite3.connect("users.db", check_same_thread=False)
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    code = generate_code()

    text = f"""
🔥 VIP Subscription

1️⃣ Payment करो

2️⃣ Screenshot लो

3️⃣ Payment proof और code भेजो

👉 {ADMIN_USERNAME}

📌 Code: {code}
"""

    await update.message.reply_text(text)


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
            f"✅ Subscription Activated\nExpiry: {expiry.date()}"
        )

        await update.message.reply_text("User Added")

    except:

        await update.message.reply_text("/add USER_ID DAYS")


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

        await update.message.reply_text("/remove USER_ID")


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT * FROM users")

    data = cur.fetchall()

    text = "Active Users:\n\n"

    for u in data:

        text += f"{u[0]} | {u[1]}\n"

    await update.message.reply_text(text)


async def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("users", users))

    print("Bot Started")

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
