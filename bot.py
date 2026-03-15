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

conn.commit()

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💎 Subscription Plans", callback_data="plans")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="mysub")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    await update.message.reply_text(
        "🔥 Welcome to VIP Subscription Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# MY SUBSCRIPTION
async def mysub(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()

    if not r:
        await q.message.reply_text("❌ No active subscription")
        return

    await q.message.reply_text(
        f"📦 Plan: {r[2]}\n📅 Join: {r[3]}\n⏳ Expiry: {r[4]}"
    )

# PLANS
async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("📈 Nitish ₹399", callback_data="plan_nitish")],
        [InlineKeyboardButton("📊 Stock ₹499", callback_data="plan_stock")],
        [InlineKeyboardButton("💹 Trader ₹499", callback_data="plan_trader")]
    ]

    await q.message.reply_text(
        "💎 Choose Plan",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# PLAN DETAIL
async def plan_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    key = q.data.split("_")[1]
    plan = PLANS[key]

    context.user_data["plan"] = key

    keyboard = [
        [InlineKeyboardButton("💳 Payment Info", callback_data="payment")],
        [InlineKeyboardButton("🎥 Demo", url=DEMO_LINK)],
        [InlineKeyboardButton("📞 Contact", url=ADMIN_CONTACT)]
    ]

    await q.message.reply_text(
        f"🔥 {plan['name']}\n💰 Price ₹{plan['price']}\n📅 Validity 30 Days",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# PAYMENT
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("📸 Send Screenshot", callback_data="send_ss")],
        [InlineKeyboardButton("🆔 Send ID", callback_data="send_id")]
    ]

    await q.message.reply_photo(
        photo=open(QR_FILE, "rb"),
        caption=f"💳 Pay via UPI\n\nUPI: {UPI}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    await q.message.reply_text("📸 Please send payment screenshot.")

async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user

    await context.bot.send_message(
        ADMIN_ID,
        f"👤 @{user.username}\n🆔 {user.id}"
    )

# SCREENSHOT
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    username = user.username if user.username else "NoUsername"
    plan = context.user_data.get("plan")

    photo = update.message.photo[-1].file_id

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{username}_{plan}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"💰 Payment Request\n\n👤 @{username}\n🆔 {user.id}\n📦 {plan}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("✅ Screenshot received. Admin approval ka wait kare.")

# APPROVE
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    data = q.data.split("_")

    uid = int(data[1])
    username = data[2]
    plan = data[3]

    join = datetime.now()
    expiry = join + timedelta(days=30)

    cur.execute(
        "INSERT INTO users VALUES (?,?,?,?,?)",
        (uid, username, plan, join.strftime("%Y-%m-%d"), expiry.strftime("%Y-%m-%d"))
    )

    conn.commit()

    invite = await context.bot.create_chat_invite_link(
        chat_id=VIP_CHANNEL,
        member_limit=1,
        expire_date=datetime.now() + timedelta(minutes=10)
    )

    await context.bot.send_message(
        uid,
        f"🎉 Subscription Activated\n\nPlan: {plan}\nJoin: {join.strftime('%Y-%m-%d')}\nExpiry: {expiry.strftime('%Y-%m-%d')}\n\n{invite.invite_link}"
    )

    await q.edit_message_caption("✅ Approved")

# REJECT
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    await context.bot.send_message(uid, "❌ Payment Rejected")

    await q.edit_message_caption("❌ Payment Rejected")

# ADMIN PANEL
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

# TOTAL USERS
async def total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]

    await q.message.reply_text(f"👥 Total Users: {total}")

# USER LIST
async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    text = ""

    for r in rows:
        text += f"{r[0]} | @{r[1]} | {r[2]}\n"

    await q.message.reply_text(text)

# EXPIRY DASHBOARD
async def expiry_dash(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    text = ""

    for r in rows:
        text += f"{r[0]} | @{r[1]} | {r[2]} | {r[4]}\n"

    await q.message.reply_text(text)

# MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

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

print("BOT RUNNING")

app.run_polling()
