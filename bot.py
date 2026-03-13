import os
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GROUP_ID = int(os.getenv("GROUP_ID"))

conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER, expiry TEXT)")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Subscription Bot")

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])
    days = int(context.args[1])

    expiry = datetime.now() + timedelta(days=days)

    cur.execute("INSERT INTO users VALUES(?,?)", (user_id, expiry))
    conn.commit()

    await update.message.reply_text("User added successfully")

async def check_expiry(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    for user in users:
        user_id = user[0]
        expiry = datetime.fromisoformat(user[1])

        if now > expiry:
            try:
                await context.bot.ban_chat_member(GROUP_ID, user_id)
            except:
                pass

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", adduser))

    app.job_queue.run_repeating(check_expiry, interval=3600, first=10)

    app.run_polling()

main()
