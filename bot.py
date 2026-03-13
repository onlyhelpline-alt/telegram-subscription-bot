import os
import sqlite3
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7066306669

UPI = "bestcourseller@ybl"
ADMIN_CONTACT = "https://t.me/ckg2754"

PLANS = {
    "nitish": {
        "name": "Nitish FX Sniper VIP",
        "price": "399",
        "channel": -1003627923608,
        "demo": "https://t.me/nitishfxvipgroup"
    },
    "stock": {
        "name": "Stock Learner Premium",
        "price": "499",
        "channel": -1003719507955,
        "demo": "https://t.me/+ZEN0OoSYehgxMmFl"
    },
    "trader": {
        "name": "Trader Paradise Exclusive",
        "price": "499",
        "channel": -1003707694192,
        "demo": "https://t.me/+fugMmeGFq5IxYmQ9"
    }
}

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER,plan TEXT,expiry TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS payments(user_id INTEGER,plan TEXT)")
conn.commit()


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💎 Subscription Plans", callback_data="plans")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="mysub")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    await update.message.reply_text(
        "🔥 VIP Subscription Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# SHOW PLANS
async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Nitish FX Sniper ₹399", callback_data="plan_nitish")],
        [InlineKeyboardButton("Stock Learner ₹499", callback_data="plan_stock")],
        [InlineKeyboardButton("Trader Paradise ₹499", callback_data="plan_trader")]
    ]

    await query.message.reply_text(
        "Choose your subscription",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# PLAN DETAILS
async def plan_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    key = query.data.split("_")[1]
    plan = PLANS[key]

    keyboard = [
        [InlineKeyboardButton("👀 Demo Channel", url=plan["demo"])],
        [InlineKeyboardButton("💳 Pay Now", callback_data=f"pay_{key}")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    await query.message.reply_text(
        f"{plan['name']}\nPrice ₹{plan['price']}\nValidity 30 Days",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# PAYMENT
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    key = query.data.split("_")[1]
    context.user_data["plan"] = key

    keyboard = [
        [InlineKeyboardButton("📤 Send Your ID To Admin", url=ADMIN_CONTACT)]
    ]

    await query.message.reply_photo(
        photo=open("qr.png", "rb"),
        caption=f"""Pay using UPI

UPI ID: {UPI}

After payment send screenshot

Your ID: {update.effective_user.id}
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# RECEIVE SCREENSHOT
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    plan = context.user_data.get("plan")

    if not plan:
        return

    photo = update.message.photo[-1].file_id

    cur.execute("INSERT INTO payments VALUES (?,?)", (user.id, plan))
    conn.commit()

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{plan}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"""💰 Payment Request

User ID: {user.id}
Plan: {PLANS[plan]['name']}
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("Payment sent for verification")


# APPROVE
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    user_id = int(data[1])
    plan = data[2]

    expiry = datetime.now() + timedelta(days=30)

    cur.execute("INSERT INTO users VALUES (?,?,?)",
                (user_id, plan, expiry.strftime("%Y-%m-%d")))

    cur.execute("DELETE FROM payments WHERE user_id=?", (user_id,))
    conn.commit()

    invite = await context.bot.create_chat_invite_link(
        PLANS[plan]["channel"],
        member_limit=1,
        expire_date=datetime.now() + timedelta(minutes=30)
    )

    await context.bot.send_message(
        user_id,
        f"""🎉 Subscription Activated

Plan: {PLANS[plan]['name']}
Expiry: {expiry}

Join Channel:
{invite.invite_link}
"""
    )

    await query.edit_message_caption("✅ Approved")


# REJECT
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = int(query.data.split("_")[1])

    cur.execute("DELETE FROM payments WHERE user_id=?", (user_id,))
    conn.commit()

    await context.bot.send_message(
        user_id,
        "❌ Payment rejected. Contact admin."
    )


# MY SUB
async def mysub(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = update.effective_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?", (user,))
    rows = cur.fetchall()

    if not rows:
        await query.message.reply_text("❌ No active subscription")
        return

    text = "Your subscriptions\n\n"

    for r in rows:
        text += f"{PLANS[r[1]]['name']} expiry {r[2]}\n"

    await query.message.reply_text(text)


# ADMIN COMMANDS
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "Admin Commands:\n\n"
        "/users\n"
        "/pending\n"
        "/broadcast\n"
        "/setexpiry USERID DAYS"
    )


# USERS COUNT
async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT DISTINCT user_id FROM users")
    count = len(cur.fetchall())

    await update.message.reply_text(f"Total users: {count}")


# PENDING PAYMENTS
async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT * FROM payments")
    rows = cur.fetchall()

    await update.message.reply_text(f"Pending payments: {len(rows)}")


# BROADCAST
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["broadcast"] = True
    await update.message.reply_text("Send message to broadcast")


async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get("broadcast"):
        return

    msg = update.message.text

    cur.execute("SELECT DISTINCT user_id FROM users")
    rows = cur.fetchall()

    for r in rows:
        try:
            await context.bot.send_message(r[0], msg)
        except:
            pass

    context.user_data["broadcast"] = False
    await update.message.reply_text("Broadcast sent")


# CHANGE EXPIRY
async def setexpiry(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:

        user_id = int(context.args[0])
        days = int(context.args[1])

        expiry = datetime.now() + timedelta(days=days)

        cur.execute(
            "UPDATE users SET expiry=? WHERE user_id=?",
            (expiry.strftime("%Y-%m-%d"), user_id)
        )

        conn.commit()

        await update.message.reply_text("Expiry updated")

    except:
        await update.message.reply_text("Usage: /setexpiry USERID DAYS")


# AUTO EXPIRY CHECK
async def expiry_check(context: ContextTypes.DEFAULT_TYPE):

    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    now = datetime.now()

    for r in rows:

        user_id = r[0]
        plan = r[1]
        exp = datetime.strptime(r[2], "%Y-%m-%d")

        if exp < now:

            await context.bot.ban_chat_member(
                PLANS[plan]["channel"],
                user_id
            )

            cur.execute("DELETE FROM users WHERE user_id=?", (user_id,))
            conn.commit()

            await context.bot.send_message(
                user_id,
                "Subscription expired\nBuy again"
            )


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("users", users))
app.add_handler(CommandHandler("pending", pending))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("setexpiry", setexpiry))

app.add_handler(CallbackQueryHandler(plans, pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail, pattern="plan_"))
app.add_handler(CallbackQueryHandler(pay, pattern="pay_"))
app.add_handler(CallbackQueryHandler(approve, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="reject_"))
app.add_handler(CallbackQueryHandler(mysub, pattern="mysub"))

app.add_handler(MessageHandler(filters.PHOTO, screenshot))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast))

job = app.job_queue
job.run_repeating(expiry_check, interval=3600)

print("BOT RUNNING")

app.run_polling()
