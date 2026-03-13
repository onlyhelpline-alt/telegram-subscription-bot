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


# ADD USER
async def adduser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id!=ADMIN_ID:
        return

    try:
        uid=int(context.args[0])
        plan=context.args[1]
        days=int(context.args[2])

        expiry=datetime.now()+timedelta(days=days)

        cur.execute("INSERT INTO users VALUES (?,?,?)",
        (uid,plan,expiry.strftime("%Y-%m-%d")))
        conn.commit()

        await update.message.reply_text("✅ User added")

    except:
        await update.message.reply_text("Usage: /adduser USERID PLAN DAYS")


# USER INFO
async def userinfo(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])

    cur.execute("SELECT * FROM users WHERE user_id=?",(uid,))
    r=cur.fetchone()

    if not r:
        await update.message.reply_text("User not found")
        return

    await update.message.reply_text(
    f"User {r[0]}\nPlan {r[1]}\nExpiry {r[2]}"
    )


# EXTEND EXPIRY (पुरानी expiry में add)
async def extend(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])
    days=int(context.args[1])

    cur.execute("SELECT expiry FROM users WHERE user_id=?",(uid,))
    row=cur.fetchone()

    if not row:
        await update.message.reply_text("User not found")
        return

    old=datetime.strptime(row[0],"%Y-%m-%d")
    new=old+timedelta(days=days)

    cur.execute("UPDATE users SET expiry=? WHERE user_id=?",
    (new.strftime("%Y-%m-%d"),uid))
    conn.commit()

    await update.message.reply_text(f"Expiry extended to {new.date()}")


# SET EXPIRY FROM TODAY
async def setexpiry(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])
    days=int(context.args[1])

    new=datetime.now()+timedelta(days=days)

    cur.execute("UPDATE users SET expiry=? WHERE user_id=?",
    (new.strftime("%Y-%m-%d"),uid))
    conn.commit()

    await update.message.reply_text(f"New expiry {new.date()}")


# SET EXACT DATE
async def setdate(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])
    date=context.args[1]

    cur.execute("UPDATE users SET expiry=? WHERE user_id=?",
    (date,uid))
    conn.commit()

    await update.message.reply_text(f"Expiry changed to {date}")


# REMOVE USER
async def removeuser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])

    cur.execute("DELETE FROM users WHERE user_id=?",(uid,))
    conn.commit()

    await update.message.reply_text("User removed")


# USERS LIST
async def userlist(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    text="📋 USER LIST\n\n"

    for r in rows:

        text+=f"""
User ID: {r[0]}
Plan: {PLANS[r[1]]['name']}
Expiry: {r[2]}
----------
"""

    await query.message.reply_text(text)


# TOTAL USERS
async def totalusers(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    await query.message.reply_text(f"Total users: {len(rows)}")


# PAYMENT HISTORY
async def payhistory(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    cur.execute("SELECT * FROM payments")
    rows=cur.fetchall()

    text="💰 PAYMENT HISTORY\n\n"

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

    text="📊 EXPIRY DASHBOARD\n\n"

    for r in rows:

        exp=datetime.strptime(r[2],"%Y-%m-%d")
        days=(exp-now).days

        text+=f"""
User {r[0]}
Plan {r[1]}
Days Left {days}
-------
"""

    await query.message.reply_text(text)


# AUTO EXPIRY
async def expiry_check(context:ContextTypes.DEFAULT_TYPE):

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    now=datetime.now()

    for r in rows:

        user_id=r[0]
        plan=r[1]
        exp=datetime.strptime(r[2],"%Y-%m-%d")

        if exp<now:

            await context.bot.ban_chat_member(
            PLANS[plan]["channel"],
            user_id
            )

            cur.execute("DELETE FROM users WHERE user_id=?",(user_id,))
            conn.commit()

            await context.bot.send_message(
            user_id,
            "Subscription expired"
            )


app=ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",adminpanel))

app.add_handler(CommandHandler("adduser",adduser))
app.add_handler(CommandHandler("removeuser",removeuser))
app.add_handler(CommandHandler("userinfo",userinfo))
app.add_handler(CommandHandler("extend",extend))
app.add_handler(CommandHandler("setexpiry",setexpiry))
app.add_handler(CommandHandler("setdate",setdate))

app.add_handler(CallbackQueryHandler(userlist,pattern="userlist"))
app.add_handler(CallbackQueryHandler(totalusers,pattern="totalusers"))
app.add_handler(CallbackQueryHandler(payhistory,pattern="payhistory"))
app.add_handler(CallbackQueryHandler(expiryboard,pattern="expiryboard"))

job=app.job_queue
job.run_repeating(expiry_check,interval=3600)

print("BOT RUNNING")

app.run_polling()
