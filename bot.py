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
QR_FILE = "qr.png"

PLANS = {
"nitish": {"name": "Nitish FX Sniper VIP", "price": "399"},
"stock": {"name": "Stock Learner Premium", "price": "499"},
"trader": {"name": "Trader Paradise Exclusive", "price": "499"}
}

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER, plan TEXT, expiry TEXT)")
conn.commit()


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💎 Subscription Plans", callback_data="plans")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="mysub")],
        [InlineKeyboardButton("💳 Payment Info", callback_data="payment")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    await update.message.reply_text(
        "🔥 Welcome to VIP Subscription Bot 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# PAYMENT SCREEN
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("📸 Send Screenshot", callback_data="send_ss")],
        [InlineKeyboardButton("🆔 Send ID To Admin", callback_data="send_id")]
    ]

    await q.message.reply_photo(
        photo=open(QR_FILE, "rb"),
        caption=f"""💳 Pay using UPI

UPI: {UPI}

📸 Send screenshot after payment
🆔 Your ID: {q.from_user.id}""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# SEND ID
async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user

    username = f"@{user.username}" if user.username else "No Username"

    await context.bot.send_message(
        ADMIN_ID,
        f"""🆔 USER INFO

Username: {username}
User ID: {user.id}"""
    )

    await q.message.reply_text("✅ ID Sent To Admin")


# SEND SCREENSHOT BUTTON
async def send_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    await q.message.reply_text("📸 Please send your payment screenshot.")


# PLANS
async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton("📈 Nitish FX Sniper ₹399", callback_data="plan_nitish")],
        [InlineKeyboardButton("📊 Stock Learner ₹499", callback_data="plan_stock")],
        [InlineKeyboardButton("💹 Trader Paradise ₹499", callback_data="plan_trader")]
    ]

    await q.message.reply_text(
        "💎 Choose your plan 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# PLAN DETAIL
async def plan_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    key = q.data.split("_")[1]
    plan = PLANS[key]

    keyboard = [
        [InlineKeyboardButton("💳 Pay Now", callback_data="payment")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    context.user_data["plan"] = key

    await q.message.reply_text(
        f"""🔥 {plan['name']}

💰 Price: ₹{plan['price']}
📅 Validity: 30 Days""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# RECEIVE SCREENSHOT
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    plan = context.user_data.get("plan")

    username = f"@{user.username}" if user.username else "No Username"

    photo = update.message.photo[-1].file_id

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{plan}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"""💰 Payment Request

👤 Username: {username}
🆔 User ID: {user.id}

📦 Plan: {plan}""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Screenshot received. Wait for approval.")


# APPROVE
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    data = q.data.split("_")
    uid = int(data[1])
    plan = data[2]

    expiry = datetime.now() + timedelta(days=30)

    cur.execute(
        "INSERT INTO users VALUES (?,?,?)",
        (uid, plan, expiry.strftime("%Y-%m-%d"))
    )
    conn.commit()

    invite = await context.bot.create_chat_invite_link(
        chat_id=VIP_CHANNEL,
        member_limit=1,
        expire_date=datetime.now() + timedelta(minutes=5)
    )

    await context.bot.send_message(
        uid,
        f"""🎉 Subscription Activated

📦 Plan: {plan}
📅 Expiry: {expiry.strftime("%Y-%m-%d")}

🔓 Join VIP Channel (valid 5 minutes)

{invite.invite_link}

⚠️ Link works only once and expires in 5 minutes."""
    )

    await q.edit_message_caption("✅ Payment Approved")


# REJECT
async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    await context.bot.send_message(
        uid,
        "❌ Payment Rejected. Please contact admin."
    )

    await q.edit_message_caption("❌ Payment Rejected")


# MY SUBSCRIPTION
async def mysub(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()

    if not r:

        keyboard = [[InlineKeyboardButton("💎 Buy Subscription", callback_data="plans")]]

        await q.message.reply_text(
            "❌ No active subscription",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    keyboard = [[InlineKeyboardButton("🔄 Renew Subscription", callback_data="plans")]]

    await q.message.reply_text(
        f"""📦 Plan: {r[1]}
📅 Expiry: {r[2]}""",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# AUTO EXPIRY
async def expiry_checker(app):

    while True:

        now = datetime.now()

        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()

        for r in rows:

            uid = r[0]
            exp = datetime.strptime(r[2], "%Y-%m-%d")

            hours = (exp - now).total_seconds() / 3600

            if 23 < hours < 24:

                try:
                    await app.bot.send_message(
                        uid,
                        "⚠️ Your subscription will expire in 24 hours"
                    )
                except:
                    pass

            if hours < 0:

                try:
                    await app.bot.ban_chat_member(VIP_CHANNEL, uid)
                    await app.bot.unban_chat_member(VIP_CHANNEL, uid)
                except:
                    pass

                cur.execute("DELETE FROM users WHERE user_id=?", (uid,))
                conn.commit()

        await asyncio.sleep(3600)


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))

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

print("🤖 BOT RUNNING")

app.run_polling()
