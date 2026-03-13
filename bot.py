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


# USER PLANS
async def plans(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    keyboard=[
    [InlineKeyboardButton("Nitish FX Sniper ₹399",callback_data="plan_nitish")],
    [InlineKeyboardButton("Stock Learner ₹499",callback_data="plan_stock")],
    [InlineKeyboardButton("Trader Paradise ₹499",callback_data="plan_trader")]
    ]

    await q.message.reply_text("Choose your subscription",reply_markup=InlineKeyboardMarkup(keyboard))


# PLAN DETAIL
async def plan_detail(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    key=q.data.split("_")[1]
    plan=PLANS[key]

    keyboard=[
    [InlineKeyboardButton("👀 Demo Channel",url=plan["demo"])],
    [InlineKeyboardButton("💳 Pay Now",callback_data=f"pay_{key}")],
    [InlineKeyboardButton("📞 Contact Admin",url=ADMIN_CONTACT)]
    ]

    await q.message.reply_text(f"{plan['name']}\nPrice ₹{plan['price']}\nValidity 30 Days",reply_markup=InlineKeyboardMarkup(keyboard))


# PAYMENT PAGE
async def payment(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    await q.message.reply_text(f"Pay using UPI\n\nUPI: {UPI}")


# PAY BUTTON
async def pay(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    key=q.data.split("_")[1]
    context.user_data["plan"]=key

    keyboard=[
    [InlineKeyboardButton("📤 Send Screenshot",callback_data="sendscreenshot")],
    [InlineKeyboardButton("👤 Send Your ID To Admin",url=ADMIN_CONTACT)]
    ]

    await q.message.reply_text(
f"""Using UPI

UPI ID: {UPI}

After payment send screenshot

Your ID: {q.from_user.id}
""",
reply_markup=InlineKeyboardMarkup(keyboard))


# SEND SCREENSHOT BUTTON
async def screenshot_button(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    await q.message.reply_text("Send screenshot now")


# RECEIVE SCREENSHOT
async def screenshot(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user
    plan=context.user_data.get("plan")

    if not plan:
        await update.message.reply_text("Please select plan first")
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
    caption=f"Payment Request\nUser ID: {user.id}\nPlan: {plan}",
    reply_markup=InlineKeyboardMarkup(keyboard)
)

    await update.message.reply_text("Payment screenshot received\nYour payment is under review")


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

    await context.bot.send_message(uid,f"Subscription Activated\nPlan:{plan}\nExpiry:{expiry}")


# REJECT
async def reject(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    uid=int(q.data.split("_")[1])

    await context.bot.send_message(uid,"Payment rejected")


# MY SUB
async def mysub(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    user=q.from_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?",(user,))
    r=cur.fetchone()

    if not r:
        await q.message.reply_text("No active subscription")
        return

    await q.message.reply_text(f"Plan:{r[1]}\nExpiry:{r[2]}")


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


# ADMIN BUTTONS
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

    if update.effective_user.id!=ADMIN_ID:
        return

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

# USER HANDLERS
app.add_handler(CallbackQueryHandler(plans,pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail,pattern="plan_"))
app.add_handler(CallbackQueryHandler(pay,pattern="pay_"))
app.add_handler(CallbackQueryHandler(payment,pattern="payment"))
app.add_handler(CallbackQueryHandler(mysub,pattern="mysub"))
app.add_handler(CallbackQueryHandler(screenshot_button,pattern="sendscreenshot"))

app.add_handler(CallbackQueryHandler(approve,pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject,pattern="reject_"))

app.add_handler(MessageHandler(filters.PHOTO,screenshot))

print("BOT RUNNING")

app.run_polling()
