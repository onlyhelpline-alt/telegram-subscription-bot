import os
import sqlite3
import asyncio
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=7066306669

UPI="bestcourseller@ybl"
ADMIN_CONTACT="https://t.me/ckg2754"

PLANS={
"nitish":{"name":"Nitish FX Sniper VIP","price":"399","channel":-1003627923608},
"stock":{"name":"Stock Learner Premium","price":"499","channel":-1003719507955},
"trader":{"name":"Trader Paradise Exclusive","price":"499","channel":-1003707694192}
}

conn=sqlite3.connect("data.db",check_same_thread=False)
cur=conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER,plan TEXT,expiry TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS payments(user_id INTEGER,plan TEXT,time TEXT)")
conn.commit()


# START
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=[
    [InlineKeyboardButton("💎 Subscription Plans",callback_data="plans")],
    [InlineKeyboardButton("📊 My Subscription",callback_data="mysub")],
    [InlineKeyboardButton("💳 Payment Info",callback_data="payment")],
    [InlineKeyboardButton("📞 Contact Admin",url=ADMIN_CONTACT)]
    ]

    await update.message.reply_text("🔥 VIP Subscription Bot",reply_markup=InlineKeyboardMarkup(keyboard))


# PAYMENT INFO
async def payment(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    await q.message.reply_text(
f"""💳 Payment Info

UPI ID: {UPI}

📤 After payment send screenshot

🆔 Your ID: {q.from_user.id}"""
)


# PLANS
async def plans(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    keyboard=[
    [InlineKeyboardButton("Nitish FX Sniper ₹399",callback_data="plan_nitish")],
    [InlineKeyboardButton("Stock Learner ₹499",callback_data="plan_stock")],
    [InlineKeyboardButton("Trader Paradise ₹499",callback_data="plan_trader")]
    ]

    await q.message.reply_text("📊 Choose your subscription",reply_markup=InlineKeyboardMarkup(keyboard))


# PLAN DETAIL
async def plan_detail(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    key=q.data.split("_")[1]
    plan=PLANS[key]

    keyboard=[
    [InlineKeyboardButton("💳 Pay Now",callback_data=f"pay_{key}")],
    [InlineKeyboardButton("📞 Contact Admin",url=ADMIN_CONTACT)]
    ]

    await q.message.reply_text(
f"""🔥 {plan['name']}

💰 Price: ₹{plan['price']}
📅 Validity: 30 Days""",
reply_markup=InlineKeyboardMarkup(keyboard))


# PAY
async def pay(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    key=q.data.split("_")[1]
    context.user_data["plan"]=key

    keyboard=[
    [InlineKeyboardButton("📤 Send Screenshot",callback_data="sendscreenshot")]
    ]

    await q.message.reply_text(
f"""💳 Pay using UPI

UPI: {UPI}

After payment send screenshot

Your ID: {q.from_user.id}""",
reply_markup=InlineKeyboardMarkup(keyboard)
)


# SCREENSHOT BUTTON
async def screenshot_button(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    await q.message.reply_text("📤 Send screenshot now")


# RECEIVE SCREENSHOT
async def screenshot(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user
    plan=context.user_data.get("plan")

    if not plan:
        await update.message.reply_text("⚠️ Please select plan first")
        return

    photo=update.message.photo[-1].file_id

    cur.execute("INSERT INTO payments VALUES (?,?,?)",(user.id,plan,str(datetime.now())))
    conn.commit()

    keyboard=[[
    InlineKeyboardButton("✅ Approve",callback_data=f"approve_{user.id}_{plan}"),
    InlineKeyboardButton("❌ Reject",callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_photo(
    ADMIN_ID,
    photo,
    caption=f"💰 Payment Request\n\nUser: {user.id}\nPlan: {plan}",
    reply_markup=InlineKeyboardMarkup(keyboard)
)

    await update.message.reply_text("📥 Screenshot received\n⏳ Payment under review")


# APPROVE
async def approve(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    data=q.data.split("_")
    uid=int(data[1])
    plan=data[2]

    expiry=datetime.now()+timedelta(days=30)

    cur.execute("INSERT INTO users VALUES (?,?,?)",(uid,plan,expiry.strftime("%Y-%m-%d")))
    conn.commit()

    await q.edit_message_caption("✅ Payment Approved")

    await context.bot.send_message(
    uid,
f"""🎉 Subscription Activated

Plan: {plan}
Expiry: {expiry}"""
)


# REJECT
async def reject(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    uid=int(q.data.split("_")[1])

    await q.edit_message_caption("❌ Payment Rejected")

    await context.bot.send_message(uid,"❌ Payment rejected")


# MY SUB
async def mysub(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    user=q.from_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?",(user,))
    r=cur.fetchone()

    if not r:
        await q.message.reply_text("❌ No active subscription")
        return

    await q.message.reply_text(
f"""📦 Plan: {r[1]}
📅 Expiry: {r[2]}"""
)


# ADMIN PANEL
async def admin(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id!=ADMIN_ID:
        return

    keyboard=[
    [InlineKeyboardButton("👥 Total Users",callback_data="totalusers")],
    [InlineKeyboardButton("📋 User List",callback_data="userlist")],
    [InlineKeyboardButton("⏳ Pending Payments",callback_data="pendingpayments")],
    [InlineKeyboardButton("📊 Expiry Dashboard",callback_data="expirydashboard")],
    [InlineKeyboardButton("💰 Payment History",callback_data="paymenthistory")]
    ]

    await update.message.reply_text("⚙️ Admin Panel",reply_markup=InlineKeyboardMarkup(keyboard))


# AUTO EXPIRY + REMINDER
async def expiry_checker(app):

    while True:

        now=datetime.now()

        cur.execute("SELECT * FROM users")
        rows=cur.fetchall()

        for r in rows:

            uid=r[0]
            plan=r[1]
            exp=datetime.strptime(r[2],"%Y-%m-%d")

            hours=(exp-now).total_seconds()/3600

            # 24h reminder
            if 23 < hours < 24:

                try:
                    await app.bot.send_message(
                    uid,
                    "⚠️ Your subscription will expire in 24 hours"
                    )
                except:
                    pass

            # expired remove
            if hours < 0:

                try:
                    await app.bot.send_message(
                    uid,
                    "❌ Your subscription has expired"
                    )
                except:
                    pass

                cur.execute("DELETE FROM users WHERE user_id=?",(uid,))
                conn.commit()

        await asyncio.sleep(3600)


# HANDLERS
app=ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",admin))

app.add_handler(CallbackQueryHandler(plans,pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail,pattern="plan_"))
app.add_handler(CallbackQueryHandler(pay,pattern="pay_"))
app.add_handler(CallbackQueryHandler(payment,pattern="payment"))
app.add_handler(CallbackQueryHandler(mysub,pattern="mysub"))
app.add_handler(CallbackQueryHandler(screenshot_button,pattern="sendscreenshot"))

app.add_handler(CallbackQueryHandler(approve,pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject,pattern="reject_"))

app.add_handler(MessageHandler(filters.PHOTO,screenshot))


async def post_init(app):

    asyncio.create_task(expiry_checker(app))


app.post_init=post_init

print("BOT RUNNING")

app.run_polling()
