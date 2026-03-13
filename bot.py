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


# PLANS
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

    await q.message.reply_text(
    f"{plan['name']}\nPrice ₹{plan['price']}\nValidity 30 Days",
    reply_markup=InlineKeyboardMarkup(keyboard)
)


# PAYMENT INFO
async def payment(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    await q.message.reply_photo(
    photo=open("qr.png","rb"),
    caption=f"Using UPI\n\nUPI ID: {UPI}\n\nAfter payment send screenshot"
)


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

    await q.message.reply_photo(
    photo=open("qr.png","rb"),
    caption=f"Pay using UPI\n\nUPI ID: {UPI}\n\nYour ID: {update.effective_user.id}",
    reply_markup=InlineKeyboardMarkup(keyboard)
)


# SCREENSHOT BUTTON
async def screenshot_button(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    await q.message.reply_text("Send payment screenshot now.")


# RECEIVE SCREENSHOT
async def screenshot(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user
    plan=context.user_data.get("plan")

    if not plan:
        await update.message.reply_text("Please select a plan first.")
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
    caption=f"💰 Payment Request\n\nUser ID: {user.id}\nPlan: {plan}\nTime: {datetime.now()}",
    reply_markup=InlineKeyboardMarkup(keyboard)
)

    await update.message.reply_text(
    "✅ Payment screenshot received\n\nYour payment is under review.\nPlease wait or contact admin."
)


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

    invite=await context.bot.create_chat_invite_link(
    PLANS[plan]["channel"],
    member_limit=1,
    expire_date=datetime.now()+timedelta(minutes=30)
)

    await context.bot.send_message(
    uid,
    f"🎉 Subscription Activated\n\nPlan: {plan}\nExpiry: {expiry}\n\nJoin:\n{invite.invite_link}"
)

    await context.bot.send_message(
    ADMIN_ID,
    f"✅ Payment Approved\nUser: {uid}\nPlan: {plan}"
)

    await q.edit_message_reply_markup(None)


# REJECT
async def reject(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    uid=int(q.data.split("_")[1])

    await context.bot.send_message(uid,"❌ Payment rejected\n\nPlease contact admin.")

    await context.bot.send_message(ADMIN_ID,f"❌ Payment Rejected\nUser: {uid}")

    await q.edit_message_reply_markup(None)


# MY SUB
async def mysub(update:Update,context:ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    uid=q.from_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?",(uid,))
    r=cur.fetchone()

    if not r:
        await q.message.reply_text("No active subscription.")
        return

    keyboard=[[InlineKeyboardButton("🔁 Renew Subscription",callback_data="plans")]]

    await q.message.reply_text(
    f"Plan: {r[1]}\nExpiry: {r[2]}",
    reply_markup=InlineKeyboardMarkup(keyboard)
)


# ADMIN COMMANDS
async def adduser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    try:
        uid=int(context.args[0])
        plan=context.args[1]
        days=int(context.args[2])
    except:
        await update.message.reply_text("Usage:\n/adduser USERID PLAN DAYS")
        return

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


async def setdate(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])
    date=context.args[1]

    cur.execute("UPDATE users SET expiry=? WHERE user_id=?",(date,uid))
    conn.commit()

    await update.message.reply_text("Expiry changed")


async def removeuser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    uid=int(context.args[0])

    cur.execute("DELETE FROM users WHERE user_id=?",(uid,))
    conn.commit()

    await update.message.reply_text("User removed")


# AUTO EXPIRY + REMINDER
async def expiry_check(context:ContextTypes.DEFAULT_TYPE):

    cur.execute("SELECT * FROM users")
    rows=cur.fetchall()

    now=datetime.now()

    for r in rows:

        uid=r[0]
        plan=r[1]
        exp=datetime.strptime(r[2],"%Y-%m-%d")

        if exp-now<=timedelta(hours=24) and exp>now:

            await context.bot.send_message(uid,"⚠️ Your subscription expires in 24 hours.")

        if exp<now:

            await context.bot.ban_chat_member(PLANS[plan]["channel"],uid)

            cur.execute("DELETE FROM users WHERE user_id=?",(uid,))
            conn.commit()

            await context.bot.send_message(uid,"Subscription expired.")


app=ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("adduser",adduser))
app.add_handler(CommandHandler("extend",extend))
app.add_handler(CommandHandler("setexpiry",setexpiry))
app.add_handler(CommandHandler("setdate",setdate))
app.add_handler(CommandHandler("removeuser",removeuser))

app.add_handler(CallbackQueryHandler(plans,pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail,pattern="plan_"))
app.add_handler(CallbackQueryHandler(pay,pattern="pay_"))
app.add_handler(CallbackQueryHandler(payment,pattern="payment"))
app.add_handler(CallbackQueryHandler(mysub,pattern="mysub"))
app.add_handler(CallbackQueryHandler(screenshot_button,pattern="sendscreenshot"))

app.add_handler(CallbackQueryHandler(approve,pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject,pattern="reject_"))

app.add_handler(MessageHandler(filters.PHOTO,screenshot))

job=app.job_queue
job.run_repeating(expiry_check,interval=3600)

print("BOT RUNNING")

app.run_polling()
