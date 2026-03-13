import os
import sqlite3
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=7066306669

UPI="bestcourseller@ybl"
ADMIN_CONTACT="https://t.me/ckg2754"

PLANS={
"nitish":{"name":"Nitish FX Sniper VIP","price":"399","channel":-1003627923608,"demo":"https://t.me/nitishfxvipgroup"},
"stock":{"name":"Stock Learner Premium","price":"499","channel":-1003719507955,"demo":"https://t.me/+ZEN0OoSYehgxMmFl"},
"trader":{"name":"Trader Paradise Exclusive","price":"499","channel":-1003707694192,"demo":"https://t.me/+fugMmeGFq5IxYmQ9"}
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


# ADMIN BUTTON HANDLERS

async def totalusers(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    await q.message.reply_text(f"Total users: {len(rows)}")


async def userlist(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    text="USER LIST\n\n"

    for r in rows:
        text+=f"{r[0]} | {r[1]} | {r[2]}\n"

    await q.message.reply_text(text)


async def pendingpayments(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM payments")
    rows=cur.fetchall()

    await q.message.reply_text(f"Pending payments: {len(rows)}")


async def paymenthistory(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM payments")
    rows=cur.fetchall()

    text="PAYMENT HISTORY\n\n"

    for r in rows:
        text+=f"{r[0]} | {r[1]} | {r[2]}\n"

    await q.message.reply_text(text)


async def expirydashboard(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    now=datetime.now()

    text="EXPIRY DASHBOARD\n\n"

    for r in rows:

        exp=datetime.strptime(r[2],"%Y-%m-%d")
        days=(exp-now).days

        text+=f"{r[0]} | {r[1]} | {days} days left\n"

    await q.message.reply_text(text)


# ADMIN COMMANDS
async def adduser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])
    plan=context.args[1]
    days=int(context.args[2])

    expiry=datetime.now()+timedelta(days=days)

    cur.execute("INSERT INTO users VALUES (?,?,?)",(uid,plan,expiry.strftime("%Y-%m-%d")))
    conn.commit()

    await update.message.reply_text("User added")


async def extend(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])
    days=int(context.args[1])

    cur.execute("SELECT expiry FROM users WHERE user_id=?",(uid,))
    row=cur.fetchone()

    old=datetime.strptime(row[0],"%Y-%m-%d")
    new=old+timedelta(days=days)

    cur.execute("UPDATE users SET expiry=? WHERE user_id=?",(new.strftime("%Y-%m-%d"),uid))
    conn.commit()

    await update.message.reply_text("Expiry extended")


async def setexpiry(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])
    days=int(context.args[1])

    new=datetime.now()+timedelta(days=days)

    cur.execute("UPDATE users SET expiry=? WHERE user_id=?",(new.strftime("%Y-%m-%d"),uid))
    conn.commit()

    await update.message.reply_text("Expiry updated")


async def removeuser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])

    cur.execute("DELETE FROM users WHERE user_id=?",(uid,))
    conn.commit()

    await update.message.reply_text("User removed")


# HANDLERS

app=ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",admin))

app.add_handler(CommandHandler("adduser",adduser))
app.add_handler(CommandHandler("extend",extend))
app.add_handler(CommandHandler("setexpiry",setexpiry))
app.add_handler(CommandHandler("removeuser",removeuser))

app.add_handler(CallbackQueryHandler(totalusers,pattern="totalusers"))
app.add_handler(CallbackQueryHandler(userlist,pattern="userlist"))
app.add_handler(CallbackQueryHandler(pendingpayments,pattern="pendingpayments"))
app.add_handler(CallbackQueryHandler(paymenthistory,pattern="paymenthistory"))
app.add_handler(CallbackQueryHandler(expirydashboard,pattern="expirydashboard"))
app.add_handler(CallbackQueryHandler(plans,pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail,pattern="plan_"))
app.add_handler(CallbackQueryHandler(pay,pattern="pay_"))
app.add_handler(CallbackQueryHandler(payment,pattern="payment"))
app.add_handler(CallbackQueryHandler(mysub,pattern="mysub"))
app.add_handler(CallbackQueryHandler(screenshot_button,pattern="sendscreenshot"))
app.add_handler(MessageHandler(filters.PHOTO,screenshot))

print("BOT RUNNING")

app.run_polling()
