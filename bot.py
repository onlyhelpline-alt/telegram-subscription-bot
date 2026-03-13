import os
import sqlite3
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        "🔥 VIP Premium Bot\n\nChoose option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# BUY
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("💳 Pay via UPI", url="upi://pay?pa=yourupi@upi&pn=VIP&am=199")]
    ]

    await query.message.reply_text(
        "Payment karo aur screenshot bhejo.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# SCREENSHOT
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    photo = update.message.photo[-1].file_id

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
    ]]

    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"Payment proof\nUser ID: {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("Screenshot received. Admin verify karega.")


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
        f"✅ Approved\nJoin Channel:\n{invite.invite_link}"
    )

    await query.edit_message_caption("User Approved")


# REJECT
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    await context.bot.send_message(
        user_id,
        "❌ Payment rejected. Contact admin."
    )

    await query.edit_message_caption("Payment Rejected")


# STATUS
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    cur.execute("SELECT expiry FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    if data:
        await query.message.reply_text(f"Expiry: {data[0]}")
    else:
        await query.message.reply_text("No active subscription")


# ADMIN PANEL
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("📊 Users", callback_data="users")],
    ]

    await update.message.reply_text(
        "Admin Dashboard",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# USERS LIST
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM users")
    data = cur.fetchall()

    text = "Active Users\n\n"

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

    await update.message.reply_text("Broadcast sent")


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
                    "⚠️ Subscription expiring soon"
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
    app.add_handler(CallbackQueryHandler(reject, pattern="reject_"))
    app.add_handler(CallbackQueryHandler(users, pattern="users"))

    app.add_handler(MessageHandler(filters.PHOTO, screenshot))

    job = app.job_queue
    job.run_repeating(check_expiry, interval=3600)

    print("Bot Running")

    await app.run_polling()


# RUN
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
