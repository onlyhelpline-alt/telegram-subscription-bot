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


# MY SUB
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


# ADMIN COMMANDS
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])
    days = int(context.args[1])

    join = datetime.now()
    expiry = join + timedelta(days=days)

    cur.execute(
        "INSERT INTO users VALUES (?,?,?,?,?)",
        (uid, "manual", "manual", join.strftime("%Y-%m-%d"), expiry.strftime("%Y-%m-%d"))
    )
    conn.commit()

    await update.message.reply_text("✅ User added")


async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])

    cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
    conn.commit()

    await update.message.reply_text("❌ User removed")


async def setexpiry(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])
    days = int(context.args[1])

    expiry = datetime.now() + timedelta(days=days)

    cur.execute(
        "UPDATE users SET expiry=? WHERE user_id=?",
        (expiry.strftime("%Y-%m-%d"), uid)
    )
    conn.commit()

    await update.message.reply_text("✅ Expiry updated")


# EXPIRY CHECKER
async def expiry_checker(app):

    while True:

        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()

        now = datetime.now()

        for r in rows:

            uid = r[0]
            exp = datetime.strptime(r[4], "%Y-%m-%d")

            remaining = exp - now

            if timedelta(hours=23) < remaining < timedelta(hours=24):

                keyboard = [[
                    InlineKeyboardButton("🔄 Renew Now", url=ADMIN_CONTACT)
                ]]

                try:
                    await app.bot.send_message(
                        uid,
                        "⚠️ Your subscription will expire in 24 hours.\nRenew now to continue access.",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except:
                    pass

            if now > exp:

                try:
                    await app.bot.ban_chat_member(VIP_CHANNEL, uid)
                    await app.bot.unban_chat_member(VIP_CHANNEL, uid)
                except:
                    pass

                cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
                conn.commit()

        await asyncio.sleep(3600)


# MAIN
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("removeuser", removeuser))
app.add_handler(CommandHandler("setexpiry", setexpiry))

app.add_handler(CallbackQueryHandler(plans, pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail, pattern="plan_"))
app.add_handler(CallbackQueryHandler(payment, pattern="payment"))
app.add_handler(CallbackQueryHandler(send_ss, pattern="send_ss"))
app.add_handler(CallbackQueryHandler(send_id, pattern="send_id"))
app.add_handler(CallbackQueryHandler(mysub, pattern="mysub"))
app.add_handler(CallbackQueryHandler(approve, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="reject_"))

app.add_handler(MessageHandler(filters.PHOTO, screenshot))

async def post_init(app):
    asyncio.create_task(expiry_checker(app))

app.post_init = post_init

print("BOT RUNNING")

app.run_polling()
