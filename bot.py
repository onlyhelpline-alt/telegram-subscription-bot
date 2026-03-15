import os
import sqlite3
import asyncio
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7066306669

VIP_CHANNEL = -1003627923608

UPI = "bestcourseller@ybl"
ADMIN_CONTACT = "https://t.me/ckg2754"
DEMO_LINK = "https://t.me/nitishfxvipgroup"
QR_FILE = "qr.png"

PLANS = {
    "nitish": {"name": "Nitish FX Sniper VIP", "price": "399"},
    "stock": {"name": "Stock Learner Premium", "price": "499"},
    "trader": {"name": "Trader Paradise Exclusive", "price": "499"}
}

# ---------------- DATABASE ----------------

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER,
username TEXT,
plan TEXT,
join_date TEXT,
expiry TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS pending(
user_id INTEGER,
username TEXT,
plan TEXT
)
""")

conn.commit()

# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💎 Subscription Plans", callback_data="plans")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="mysub")],
        [InlineKeyboardButton("💳 Payment Info", callback_data="payment")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    await update.message.reply_text(
        "🔥 Welcome to VIP Subscription Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- ADMIN PANEL ----------------

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("👥 Total Users", callback_data="total_users")],
        [InlineKeyboardButton("📋 User List", callback_data="user_list")],
        [InlineKeyboardButton("📊 Expiry Dashboard", callback_data="expiry_dash")]
    ]

    await update.message.reply_text(
        "⚙️ Admin Panel",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- ADMIN COMMANDS ----------------

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        plan = context.args[1]
        days = int(context.args[2])
    except:
        await update.message.reply_text(
            "Usage:\n/adduser USER_ID PLAN DAYS\nExample:\n/adduser 123456789 nitish 30"
        )
        return

    join = datetime.now()
    expiry = join + timedelta(days=days)

    cur.execute(
        "INSERT INTO users VALUES (?,?,?,?,?)",
        (uid, "manual", plan, join.strftime("%Y-%m-%d"), expiry.strftime("%Y-%m-%d"))
    )
    conn.commit()

    await update.message.reply_text(
        f"✅ User Added\nUser ID: {uid}\nPlan: {plan}\nExpiry: {expiry.strftime('%Y-%m-%d')}"
    )

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
    except:
        await update.message.reply_text(
            "Usage:\n/removeuser USER_ID\nExample:\n/removeuser 123456789"
        )
        return

    cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
    conn.commit()

    try:
        await context.bot.ban_chat_member(VIP_CHANNEL, uid)
        await context.bot.unban_chat_member(VIP_CHANNEL, uid)
    except:
        pass

    await update.message.reply_text("✅ User removed")

async def extend(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        days = int(context.args[1])
    except:
        await update.message.reply_text(
            "Usage:\n/extend USER_ID DAYS\nExample:\n/extend 123456789 10"
        )
        return

    cur.execute("SELECT expiry FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()

    if not r:
        await update.message.reply_text("User not found")
        return

    old_exp = datetime.strptime(r[0], "%Y-%m-%d")
    new_exp = old_exp + timedelta(days=days)

    cur.execute(
        "UPDATE users SET expiry=? WHERE user_id=?",
        (new_exp.strftime("%Y-%m-%d"), uid)
    )
    conn.commit()

    await update.message.reply_text(
        f"⏳ Expiry extended\nNew expiry: {new_exp.strftime('%Y-%m-%d')}"
    )

async def setexpiry(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        new_exp = context.args[1]
    except:
        await update.message.reply_text(
            "Usage:\n/setexpiry USER_ID YYYY-MM-DD\nExample:\n/setexpiry 123456789 2026-05-01"
        )
        return

    cur.execute(
        "UPDATE users SET expiry=? WHERE user_id=?",
        (new_exp, uid)
    )
    conn.commit()

    await update.message.reply_text(f"📅 Expiry updated to {new_exp}")

# ---------------- PAYMENT INFO ----------------

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("📸 After payment Send Screenshot", callback_data="send_ss")],
        [InlineKeyboardButton("🆔 Send Your ID to Admin", callback_data="send_id")]
    ]

    await q.message.reply_photo(
        photo=open(QR_FILE, "rb"),
        caption=f"💳 Pay via UPI\n\nUPI: {UPI}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    await q.message.reply_text(
        "📸 Please send payment screenshot.\n\n⏳ Your request will be sent to admin for approval."
    )

async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user

    await context.bot.send_message(
        ADMIN_ID,
        f"🆔 USER INFO\n\nUsername: @{user.username}\nUser ID: {user.id}"
    )

# ---------------- PLANS ----------------

async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("📈 Nitish FX Sniper ₹399", callback_data="plan_nitish")],
        [InlineKeyboardButton("📊 Stock Learner ₹499", callback_data="plan_stock")],
        [InlineKeyboardButton("💹 Trader Paradise ₹499", callback_data="plan_trader")]
    ]

    await q.message.reply_text(
        "💎 Choose your plan",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- PLAN DETAIL ----------------

async def plan_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    key = q.data.split("_")[1]
    plan = PLANS[key]

    context.user_data["plan"] = key

    keyboard = [
        [InlineKeyboardButton("💳 Pay Now", callback_data="payment")],
        [InlineKeyboardButton("🎥 Check Demo", url=DEMO_LINK)],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    await q.message.reply_text(
f"""
🔥 {plan['name']}

💰 Price: ₹{plan['price']}
📅 Validity: 30 Days
""",
reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- SCREENSHOT ----------------

async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    username = user.username if user.username else "NoUsername"
    plan = context.user_data.get("plan")

    photo = update.message.photo[-1].file_id

    cur.execute(
        "INSERT INTO pending VALUES (?,?,?)",
        (user.id, username, plan)
    )
    conn.commit()

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{plan}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"""
💰 Payment Request

👤 Username: @{username}
🆔 User ID: {user.id}
📦 Plan: {plan}
""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        "✅ Screenshot received.\n\n⏳ Please wait for admin approval."
    )

# ---------------- APPROVE ----------------

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    data = q.data.split("_")
    uid = int(data[1])
    plan = data[2]

    join = datetime.now()
    expiry = join + timedelta(days=30)

    cur.execute("SELECT username FROM pending WHERE user_id=?", (uid,))
    uname = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO users VALUES (?,?,?,?,?)",
        (uid, uname, plan, join.strftime("%Y-%m-%d"), expiry.strftime("%Y-%m-%d"))
    )
    conn.commit()

    invite = await context.bot.create_chat_invite_link(
        chat_id=VIP_CHANNEL,
        member_limit=1
    )

    await context.bot.send_message(
        uid,
f"""
🎉 Subscription Activated

📦 Plan: {plan}
📅 Join: {join.strftime("%Y-%m-%d")}
⏳ Expiry: {expiry.strftime("%Y-%m-%d")}

🔗 Join VIP Channel
{invite.invite_link}
"""
    )

    await q.edit_message_caption("✅ Payment Approved")

# ---------------- REJECT ----------------

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    await context.bot.send_message(uid, "❌ Payment Rejected")

# ---------------- AUTO EXPIRY ----------------

async def expiry_checker(app):

    while True:

        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()

        now = datetime.now()

        for r in rows:

            exp = datetime.strptime(r[4], "%Y-%m-%d")

            if now > exp:

                uid = r[0]

                try:
                    await app.bot.ban_chat_member(VIP_CHANNEL, uid)
                    await app.bot.unban_chat_member(VIP_CHANNEL, uid)
                except:
                    pass

                cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
                conn.commit()

        await asyncio.sleep(3600)

# ---------------- MAIN ----------------

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("removeuser", removeuser))
app.add_handler(CommandHandler("extend", extend))
app.add_handler(CommandHandler("setexpiry", setexpiry))

app.add_handler(CallbackQueryHandler(plans, pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail, pattern="plan_"))

app.add_handler(CallbackQueryHandler(payment, pattern="payment"))
app.add_handler(CallbackQueryHandler(send_ss, pattern="send_ss"))
app.add_handler(CallbackQueryHandler(send_id, pattern="send_id"))
app.add_handler(CallbackQueryHandler(mysub, pattern="mysub"))

app.add_handler(CallbackQueryHandler(total_users, pattern="total_users"))
app.add_handler(CallbackQueryHandler(user_list, pattern="user_list"))
app.add_handler(CallbackQueryHandler(expiry_dash, pattern="expiry_dash"))

app.add_handler(CallbackQueryHandler(approve, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="reject_"))

app.add_handler(MessageHandler(filters.PHOTO, screenshot))


async def post_init(app):
    asyncio.create_task(expiry_checker(app))


app.post_init = post_init

print("BOT RUNNING")

app.run_polling()
