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
        [InlineKeyboardButton("💳 Payment Info", callback_data="payment")],
        [InlineKeyboardButton("📞 Contact Admin", url=ADMIN_CONTACT)]
    ]

    await update.message.reply_text(
        "🔥 Welcome to VIP Subscription Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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

    text = "📋 USER LIST\n\n"

    for r in rows:
        text += f"👤 @{r[1]}\n🆔 {r[0]}\n📦 {r[2]}\n\n"

    await q.message.reply_text(text)

# EXPIRY DASHBOARD

async def expiry_dash(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    text = "📊 EXPIRY DASHBOARD\n\n"

    for r in rows:

        text += f"""👤 @{r[1]}
🆔 {r[0]}
📦 {r[2]}
📅 Join: {r[3]}
⏳ Expiry: {r[4]}

"""

    await q.message.reply_text(text)

# ADD USER

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])
    plan = context.args[1]
    days = int(context.args[2])

    join = datetime.now()
    expiry = join + timedelta(days=days)

    cur.execute(
        "INSERT INTO users VALUES (?,?,?,?,?)",
        (uid, "manual", plan, join.strftime("%Y-%m-%d"), expiry.strftime("%Y-%m-%d"))
    )

    conn.commit()

    await update.message.reply_text(
        f"✅ User Added\nID: {uid}\nPlan: {plan}\nExpiry: {expiry.strftime('%Y-%m-%d')}"
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

    await q.message.reply_text(
        "📸 Please send payment screenshot.\n\n⏳ Admin ko screenshot receive ho gaya hai.\nApproval ke liye wait kare."
    )

async def send_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user

    await context.bot.send_message(
        ADMIN_ID,
        f"👤 @{user.username}\n🆔 {user.id}"
    )

# PLAN LIST

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
        [InlineKeyboardButton("💳 Pay Now", callback_data="payment")],
        [InlineKeyboardButton("🎥 Demo", url=DEMO_LINK)],
        [InlineKeyboardButton("📞 Contact", url=ADMIN_CONTACT)]
    ]

    await q.message.reply_text(
f"🔥 {plan['name']}\n💰 Price ₹{plan['price']}\n📅 Validity 30 Days",
reply_markup=InlineKeyboardMarkup(keyboard)
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

    await update.message.reply_text(
        "✅ Screenshot received.\n⏳ Admin approval ka wait kare."
    )

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
f"""🎉 Congratulations!

📦 Plan: {plan}
📅 Join: {join.strftime("%Y-%m-%d")}
⏳ Expiry: {expiry.strftime("%Y-%m-%d")}

🔗 Join Channel
{invite.invite_link}
"""
    )

    await q.edit_message_caption(
f"""✅ APPROVED

👤 @{username}
🆔 {uid}

📦 Plan: {plan}
📅 Join: {join.strftime("%Y-%m-%d")}
⏳ Expiry: {expiry.strftime("%Y-%m-%d")}
"""
    )

# REJECT

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    await context.bot.send_message(uid,"❌ Payment Rejected")

    await q.edit_message_caption("❌ Payment Rejected")

# BROADCAST

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    msg = update.message.reply_to_message

    sent = 0

    for u in users:
        try:
            await msg.copy(u[0])
            sent += 1
        except:
            pass

    await update.message.reply_text(f"Broadcast sent to {sent} users")

# EXPIRY CHECKER

async def expiry_checker(app):

    while True:

        cur.execute("SELECT * FROM users")
        rows = cur.fetchall()

        now = datetime.now()

        for r in rows:

            uid = r[0]
            exp = datetime.strptime(r[4], "%Y-%m-%d")

            # 24h reminder
            if exp - now < timedelta(hours=24) and exp - now > timedelta(hours=23):

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
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("broadcast", broadcast))

app.add_handler(CallbackQueryHandler(plans, pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail, pattern="plan_"))
app.add_handler(CallbackQueryHandler(payment, pattern="payment"))
app.add_handler(CallbackQueryHandler(send_ss, pattern="send_ss"))
app.add_handler(CallbackQueryHandler(send_id, pattern="send_id"))
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
