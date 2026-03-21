from telegram import *
from telegram.ext import *
from datetime import datetime, timedelta

from config import *
from database import *

init_db()

user_data_map = {}

# ================= START =================
async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("💎 Subscription Plans", callback_data="plans")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="mysub")],
        [InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    await update.message.reply_text("🔥 Welcome to VIP Subscription Bot", reply_markup=InlineKeyboardMarkup(kb))


# ================= PLANS =================
PLANS = {
    "nitish": ("Nitish Apex", 399, 30),
    "stock": ("Stock Learner", 499, 30),
    "trader": ("Trader Pro", 499, 30)
}

async def plans(update: Update, context):
    q = update.callback_query
    await q.answer()

    kb = []
    for key, val in PLANS.items():
        kb.append([InlineKeyboardButton(f"{val[0]} ₹{val[1]}", callback_data=f"plan_{key}")])

    await q.message.reply_text("💎 Choose Plan", reply_markup=InlineKeyboardMarkup(kb))


# ================= PLAN DETAIL =================
async def plan_detail(update: Update, context):
    q = update.callback_query
    await q.answer()

    key = q.data.split("_")[1]
    name, price, validity = PLANS[key]

    context.user_data["plan"] = key

    kb = [
        [InlineKeyboardButton("💰 Payment Info", callback_data="payinfo")],
        [InlineKeyboardButton("🎬 Demo", url="https://example.com")],
        [InlineKeyboardButton("📞 Contact", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]

    await q.message.reply_text(
        f"📦 {name}\n💰 ₹{price}\n⏳ {validity} Days",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= PAYMENT INFO =================
async def payinfo(update: Update, context):
    q = update.callback_query
    await q.answer()

    key = context.user_data["plan"]
    name, price, validity = PLANS[key]

    await context.bot.send_photo(
        chat_id=q.from_user.id,
        photo=open("qr.png", "rb"),
        caption=f"""
💰 Payment Info

📦 Plan: {name}
💵 Amount: ₹{price}

UPI: {UPI_ID}
"""
    )

    kb = [
        [InlineKeyboardButton("📸 Send Screenshot", callback_data="send_ss")],
        [InlineKeyboardButton("🆔 Send ID", callback_data="send_id")]
    ]

    await q.message.reply_text("Choose Option", reply_markup=InlineKeyboardMarkup(kb))


# ================= SEND ID =================
async def send_id(update: Update, context):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    key = context.user_data["plan"]
    name, price, _ = PLANS[key]

    await context.bot.send_message(
        ADMIN_ID,
        f"""
🆔 ID REQUEST

👤 @{user.username}
🆔 {user.id}
📦 {name}
💰 ₹{price}
"""
    )

    await q.message.reply_text("✅ Your ID sent to admin")


# ================= SEND SCREENSHOT =================
async def send_ss(update: Update, context):
    q = update.callback_query
    await q.answer()

    context.user_data["awaiting_ss"] = True
    await q.message.reply_text("📸 Send your payment screenshot")


# ================= HANDLE PHOTO =================
async def photo(update: Update, context):
    if not context.user_data.get("awaiting_ss"):
        return

    user = update.message.from_user
    key = context.user_data["plan"]
    name, price, validity = PLANS[key]

    kb = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{key}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]

    await context.bot.send_photo(
        ADMIN_ID,
        update.message.photo[-1].file_id,
        caption=f"""
💰 Payment Screenshot

👤 @{user.username}
🆔 {user.id}
📦 {name}
💰 ₹{price}
⏳ {validity} Days
""",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    await update.message.reply_text("✅ Screenshot sent to admin, wait for approval")


# ================= APPROVE =================
async def approve(update: Update, context):
    q = update.callback_query
    await q.answer()

    data = q.data.split("_")
    uid = int(data[1])
    key = data[2]

    name, price, validity = PLANS[key]

    now = datetime.now()
    exp = now + timedelta(days=validity)

    user = await context.bot.get_chat(uid)

    add_user(
        uid,
        user.username or "NoUsername",
        name,
        price,
        now.strftime("%Y-%m-%d"),
        exp.strftime("%Y-%m-%d")
    )

    link = await context.bot.create_chat_invite_link(
        chat_id=VIP_CHANNEL_ID,
        member_limit=1
    )

    await context.bot.send_message(
        uid,
        f"""
🎉 Congratulations!

📦 Plan: {name}
📅 Join: {now.date()}
⏳ Expiry: {exp.date()}

🔗 Join: {link.invite_link}
"""
    )

    await q.edit_message_reply_markup(None)


# ================= REJECT =================
async def reject(update: Update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    await context.bot.send_message(
        uid,
        "❌ Your payment was rejected. Contact admin."
    )

    await q.edit_message_reply_markup(None)


# ================= MY SUB =================
async def my(update: Update, context):
    q = update.callback_query
    await q.answer()

    for u in get_users():
        if u[0] == q.from_user.id:
            await q.message.reply_text(f"""
📦 Plan: {u[2]}
💰 Price: ₹{u[3]}
📅 Join: {u[4]}
⏳ Expiry: {u[5]}
""")
            return

    await q.message.reply_text("❌ No active subscription")


# ================= ADMIN =================
async def admin(update: Update, context):
    if update.message.from_user.id != ADMIN_ID:
        return

    await update.message.reply_text("""
⚙️ ADMIN PANEL

Use:
/approve user_id plan_key
""")


# ================= EXPIRY =================
async def expiry(context):
    for u in get_users():
        uid = u[0]
        exp = datetime.strptime(u[5], "%Y-%m-%d")
        now = datetime.now()

        if now > exp:
            remove_user(uid)


# ================= APP =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(CallbackQueryHandler(plans, pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail, pattern="plan_"))
app.add_handler(CallbackQueryHandler(payinfo, pattern="payinfo"))
app.add_handler(CallbackQueryHandler(send_id, pattern="send_id"))
app.add_handler(CallbackQueryHandler(send_ss, pattern="send_ss"))
app.add_handler(CallbackQueryHandler(approve, pattern="approve_"))
app.add_handler(CallbackQueryHandler(reject, pattern="reject_"))
app.add_handler(CallbackQueryHandler(my, pattern="mysub"))

app.add_handler(MessageHandler(filters.PHOTO, photo))

app.job_queue.run_repeating(expiry, interval=3600)

app.run_polling()
