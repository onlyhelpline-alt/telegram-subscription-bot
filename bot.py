import os
import sqlite3
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# DATABASE
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
expiry TEXT
)
""")
conn.commit()

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💎 Buy Premium", callback_data="buy")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="status")]
    ]

    await update.message.reply_text(
        "🔥 VIP Premium Bot\n\nExclusive course access.\n\nChoose option below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# BUY BUTTON
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💳 Pay via UPI", url="upi://pay?pa=yourupi@upi&pn=VIP&am=199")]
    ]

    await query.message.reply_text(
        "💳 Complete payment.\n\nAfter payment upload screenshot.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# RECEIVE SCREENSHOT
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    photo = update.message.photo[-1].file_id

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ]

    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"Payment proof from user\nID: {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ Screenshot received.\nAdmin verification pending.")

# APPROVE
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    expiry = datetime.now() + timedelta(days=30)

    cur.execute(
        "INSERT OR REPLACE INTO users VALUES (?,?)",
        (user_id, expiry.strftime("%Y-%m-%d"))
    )

    conn.commit()

    invite = await context.bot.create_chat_invite_link(
        CHANNEL_ID,
        member_limit=1
    )

    await context.bot.send_message(
        user_id,
        f"✅ Payment Verified\n\nJoin Channel:\n{invite.invite_link}"
    )

    await query.edit_message_caption("User Approved")

# STATUS
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    cur.execute("SELECT expiry FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    if data:
        await query.message.reply_text(f"📅 Expiry Date: {data[0]}")
    else:
        await query.message.reply_text("❌ No active subscription")

# ADMIN DASHBOARD
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("📊 Users List", callback_data="users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
    ]

    await update.message.reply_text(
        "⚙️ Admin Dashboard",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# USERS
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM users")
    data = cur.fetchall()

    text = "👥 Active Subscribers\n\n"

    for u in data:
        text += f"{u[0]} | {u[1]}\n"

    await query.message.reply_text(text)

# BROADCAST
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    for u in users:
        try:
            await context.bot.send_message(u[0], msg)
        except:
            pass

    await update.message.reply_text("✅ Broadcast Sent")

# AUTO EXPIRY
async def check_expiry(context: ContextTypes.DEFAULT_TYPE):

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    now = datetime.now()

    for u in users:

        user_id = u[0]
        expiry = datetime.strptime(u[1], "%Y-%m-%d")

        if expiry < now:

            await context.bot.ban_chat_member(CHANNEL_ID, user_id)

            cur.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit()

        elif expiry - now <= timedelta(days=1):

            try:
                await context.bot.send_message(
                    user_id,
                    "⚠️ Subscription expiring tomorrow\nRenew now."
                )
            except:
                pass

# MAIN
async def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(CallbackQueryHandler(buy, pattern="buy"))
    app.add_handler(CallbackQueryHandler(status, pattern="status"))
    app.add_handler(CallbackQueryHandler(approve, pattern="approve_"))
    app.add_handler(CallbackQueryHandler(users, pattern="users"))

    app.add_handler(MessageHandler(filters.PHOTO, screenshot))

    job = app.job_queue
    job.run_repeating(check_expiry, interval=3600)

    print("Bot Running")

    await app.run_polling()

# RUN
if __name__ == "__main__":

    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
