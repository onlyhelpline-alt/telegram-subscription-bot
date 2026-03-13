import os
import sqlite3
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7066306669

PLANS = {
"nitish": {
"name": "Nitish FX Sniper VIP",
"price": "399",
"channel": -1003627923608,
"demo": "https://t.me/nitishfxvipgroup"
},

"stock": {
"name": "Stock Learner Premium",
"price": "499",
"channel": -1003719507955,
"demo": "https://t.me/+ZEN0OoSYehgxMmFl"
},

"trader": {
"name": "Trading Paradise Exclusive",
"price": "499",
"channel": -1003707694192,
"demo": "https://t.me/+fugMmeGFq5IxYmQ9"
}
}

UPI = "bestcourseller@ybl"
ADMIN_CONTACT = "@ckg2754"

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
user_id INTEGER,
plan TEXT,
expiry TEXT
)""")

conn.commit()

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    keyboard=[
[InlineKeyboardButton("💎 Subscription Plans",callback_data="plans")],
[InlineKeyboardButton("📊 My Subscription",callback_data="mysub")],
[InlineKeyboardButton("📞 Contact Admin",url="https://t.me/ckg2754")]
]

    await update.message.reply_text(
"🔥 VIP Subscription Bot",
reply_markup=InlineKeyboardMarkup(keyboard)
)

async def plans(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    keyboard=[
[InlineKeyboardButton("📈 Nitish FX Sniper VIP",callback_data="plan_nitish")],
[InlineKeyboardButton("📊 Stock Learner Premium",callback_data="plan_stock")],
[InlineKeyboardButton("🚀 Trading Paradise",callback_data="plan_trader")]
]

    await query.message.reply_text(
"Choose your subscription",
reply_markup=InlineKeyboardMarkup(keyboard)
)

async def plan_detail(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    key=query.data.split("_")[1]

    plan=PLANS[key]

    keyboard=[
[InlineKeyboardButton("👀 Demo Channel",url=plan["demo"])],
[InlineKeyboardButton("💳 Pay Now",callback_data=f"pay_{key}")],
[InlineKeyboardButton("📞 Contact Admin",url="https://t.me/ckg2754")]
]

    await query.message.reply_text(
f"{plan['name']}\nPrice ₹{plan['price']}\nValidity 30 Days",
reply_markup=InlineKeyboardMarkup(keyboard)
)

async def pay(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    key=query.data.split("_")[1]

    context.user_data["plan"]=key

    await query.message.reply_photo(
photo=open("qr.png","rb"),
caption=f"Pay using UPI\n\nUPI ID:\n{UPI}\n\nAfter payment send screenshot"
)

async def screenshot(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user

    plan=context.user_data.get("plan")

    if not plan:
        return

    photo=update.message.photo[-1].file_id

    keyboard=[[

InlineKeyboardButton("✅ Approve",callback_data=f"approve_{user.id}_{plan}"),
InlineKeyboardButton("❌ Reject",callback_data=f"reject_{user.id}")

]]

    await context.bot.send_photo(
ADMIN_ID,
photo,
caption=f"Payment request\nUser {user.id}\nPlan {plan}",
reply_markup=InlineKeyboardMarkup(keyboard)
)

    await update.message.reply_text("Payment sent for verification")

async def approve(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    data=query.data.split("_")

    user_id=int(data[1])
    plan=data[2]

    expiry=datetime.now()+timedelta(days=30)

    cur.execute(
"INSERT INTO users VALUES (?,?,?)",
(user_id,plan,expiry.strftime("%Y-%m-%d"))
)

    conn.commit()

    invite=await context.bot.create_chat_invite_link(

PLANS[plan]["channel"],
member_limit=1,
expire_date=datetime.now()+timedelta(minutes=30)

)

    await context.bot.send_message(

user_id,

f"🎉 Subscription Activated\n\nPlan {PLANS[plan]['name']}\nExpiry {expiry}\n\nJoin\n{invite.invite_link}"

)

async def reject(update:Update,context:ContextTypes.DEFAULT_TYPE):

    query=update.callback_query
    await query.answer()

    user_id=int(query.data.split("_")[1])

    await context.bot.send_message(
user_id,
"Payment rejected contact admin"
)

async def mysub(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user.id

    cur.execute("SELECT * FROM users WHERE user_id=?",(user,))
    rows=cur.fetchall()

    if not rows:
        await update.message.reply_text("No subscription")
        return

    text="Your subscriptions\n\n"

    for r in rows:

        text+=f"{PLANS[r[1]]['name']} expiry {r[2]}\n"

    await update.message.reply_text(text)

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

f"Subscription expired\n\nBuy again\n\nContact {ADMIN_CONTACT}"

)

app=ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("mysub",mysub))

app.add_handler(CallbackQueryHandler(plans,pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail,pattern="plan_"))
app.add_handler(CallbackQueryHandler(pay,pattern="pay_"))
app.add_handler(CallbackQueryHandler(approve,pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject,pattern="reject_"))

app.add_handler(MessageHandler(filters.PHOTO,screenshot))

job=app.job_queue
job.run_repeating(expiry_check,interval=3600)

print("BOT RUNNING")

app.run_polling()
