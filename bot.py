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
"nitish":{
"name":"Nitish FX Sniper VIP",
"price":"399",
"channel":-1003627923608,
"demo":"https://t.me/nitishfxvipgroup"
},
"stock":{
"name":"Stock Learner Premium",
"price":"499",
"channel":-1003719507955,
"demo":"https://t.me/+ZEN0OoSYehgxMmFl"
},
"trader":{
"name":"Trader Paradise Exclusive",
"price":"499",
"channel":-1003707694192,
"demo":"https://t.me/+fugMmeGFq5IxYmQ9"
}
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

    await update.message.reply_text(
    "🔥 VIP Subscription Bot",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

# SHOW PLANS
async def plans(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    keyboard=[
    [InlineKeyboardButton("Nitish FX Sniper ₹399",callback_data="plan_nitish")],
    [InlineKeyboardButton("Stock Learner ₹499",callback_data="plan_stock")],
    [InlineKeyboardButton("Trader Paradise ₹499",callback_data="plan_trader")]
    ]

    await query.message.reply_text(
    "Choose your subscription",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

# PLAN DETAIL
async def plan_detail(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    key=query.data.split("_")[1]
    plan=PLANS[key]

    keyboard=[
    [InlineKeyboardButton("👀 Demo Channel",url=plan["demo"])],
    [InlineKeyboardButton("💳 Pay Now",callback_data=f"pay_{key}")],
    [InlineKeyboardButton("📞 Contact Admin",url=ADMIN_CONTACT)]
    ]

    await query.message.reply_text(
    f"{plan['name']}\nPrice ₹{plan['price']}\nValidity 30 Days",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

# PAYMENT INFO
async def paymentinfo(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    keyboard=[
    [InlineKeyboardButton("📤 Send Screenshot",callback_data="sendscreenshot")],
    [InlineKeyboardButton("👤 Send Your ID To Admin",url=ADMIN_CONTACT)]
    ]

    await query.message.reply_text(
f"""Using UPI

UPI ID: {UPI}

After payment send screenshot

Your ID: {query.from_user.id}
""",
reply_markup=InlineKeyboardMarkup(keyboard)
)

# PAY
async def pay(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    plan=query.data.split("_")[1]
    context.user_data["plan"]=plan

    keyboard=[
    [InlineKeyboardButton("📤 Send Screenshot",callback_data="sendscreenshot")],
    [InlineKeyboardButton("👤 Send Your ID To Admin",url=ADMIN_CONTACT)]
    ]

    await query.message.reply_text(
f"""Using UPI

UPI ID: {UPI}

After payment send screenshot

Your ID: {query.from_user.id}
""",
reply_markup=InlineKeyboardMarkup(keyboard)
)

# SCREENSHOT BUTTON
async def screenshot_button(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    await query.message.reply_text("Please send payment screenshot now.")

# RECEIVE SCREENSHOT
async def screenshot(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user
    plan=context.user_data.get("plan")

    if not plan:
        await update.message.reply_text("Select plan first.")
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
    caption=f"""💰 Payment Request

User ID: {user.id}
Plan: {PLANS[plan]['name']}
""",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("Payment sent for verification.")

# APPROVE
async def approve(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    data=query.data.split("_")
    uid=int(data[1])
    plan=data[2]

    expiry=datetime.now()+timedelta(days=30)

    cur.execute("INSERT INTO users VALUES (?,?,?)",
    (uid,plan,expiry.strftime("%Y-%m-%d")))
    conn.commit()

    invite=await context.bot.create_chat_invite_link(
    PLANS[plan]["channel"],
    member_limit=1,
    expire_date=datetime.now()+timedelta(minutes=30)
    )

    await context.bot.send_message(
    uid,
f"""🎉 Subscription Activated

Plan: {PLANS[plan]['name']}
Expiry: {expiry.date()}

Join Channel:
{invite.invite_link}
"""
)

    await query.edit_message_reply_markup(None)

# REJECT
async def reject(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    uid=int(query.data.split("_")[1])

    await context.bot.send_message(
    uid,
"❌ Payment rejected. Contact admin."
)

    await query.edit_message_reply_markup(None)

# MY SUB
async def mysub(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    uid=query.from_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?",(uid,))
    rows=cur.fetchall()

    if not rows:
        await query.message.reply_text("No subscription")
        return

    text="Your Subscription\n\n"

    for r in rows:

        text+=f"""
Plan: {PLANS[r[1]]['name']}
Expiry: {r[2]}
-------
"""

    await query.message.reply_text(text)

# ADMIN PANEL
async def adminpanel(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id!=ADMIN_ID:
        return

    keyboard=[
    [InlineKeyboardButton("👥 Total Users",callback_data="totalusers")],
    [InlineKeyboardButton("📋 User List",callback_data="userlist")],
    [InlineKeyboardButton("⏳ Pending Payments",callback_data="pendingpanel")],
    [InlineKeyboardButton("📊 Expiry Dashboard",callback_data="expiryboard")],
    [InlineKeyboardButton("💰 Payment History",callback_data="payhistory")]
    ]

    await update.message.reply_text(
    "⚙️ Admin Panel",
    reply_markup=InlineKeyboardMarkup(keyboard)
    )

# TOTAL USERS
async def totalusers(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    await query.message.reply_text(f"Total users: {len(rows)}")

# USER LIST
async def userlist(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    text="USER LIST\n\n"

    for r in rows:

        text+=f"""
User {r[0]}
Plan {r[1]}
Expiry {r[2]}
-------
"""

    await query.message.reply_text(text)

# PENDING PAYMENTS
async def pendingpanel(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM payments")
    rows=cur.fetchall()

    await query.message.reply_text(f"Pending payments: {len(rows)}")

# PAYMENT HISTORY
async def payhistory(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM payments")
    rows=cur.fetchall()

    text="Payment History\n\n"

    for r in rows:

        text+=f"""
User {r[0]}
Plan {r[1]}
Time {r[2]}
-------
"""

    await query.message.reply_text(text)

# EXPIRY DASHBOARD
async def expiryboard(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    now=datetime.now()

    text="Expiry Dashboard\n\n"

    for r in rows:

        exp=datetime.strptime(r[2],"%Y-%m-%d")
        days=(exp-now).days

        text+=f"""
User {r[0]}
Plan {r[1]}
Days left {days}
-------
"""

    await query.message.reply_text(text)

# AUTO EXPIRY
async def expiry_check(context:ContextTypes.DEFAULT_TYPE):

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    now=datetime.now()

    for r in rows:

        uid=r[0]
        plan=r[1]
        exp=datetime.strptime(r[2],"%Y-%m-%d")

        if exp<now:

            await context.bot.ban_chat_member(
            PLANS[plan]["channel"],
            uid
            )

            cur.execute("DELETE FROM users WHERE user_id=?",(uid,))
            conn.commit()

            await context.bot.send_message(uid,"Subscription expired")

app=ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",adminpanel))

app.add_handler(CallbackQueryHandler(plans,pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail,pattern="plan_"))
app.add_handler(CallbackQueryHandler(paymentinfo,pattern="payment"))
app.add_handler(CallbackQueryHandler(pay,pattern="pay_"))
app.add_handler(CallbackQueryHandler(mysub,pattern="mysub"))

app.add_handler(CallbackQueryHandler(userlist,pattern="userlist"))
app.add_handler(CallbackQueryHandler(totalusers,pattern="totalusers"))
app.add_handler(CallbackQueryHandler(pendingpanel,pattern="pendingpanel"))
app.add_handler(CallbackQueryHandler(payhistory,pattern="payhistory"))
app.add_handler(CallbackQueryHandler(expiryboard,pattern="expiryboard"))

app.add_handler(CallbackQueryHandler(approve,pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject,pattern="reject_"))
app.add_handler(CallbackQueryHandler(screenshot_button,pattern="sendscreenshot"))

app.add_handler(MessageHandler(filters.PHOTO,screenshot))

job=app.job_queue
job.run_repeating(expiry_check,interval=3600)

print("BOT RUNNING")

app.run_polling()
