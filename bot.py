from telegram import *
from telegram.ext import *
from datetime import datetime, timedelta

from config import *
from database import *

init_db()

user_state = {}

# ================= START (SAME UI) =================
async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("💎 VIP Group List", callback_data="plans")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="my")],
        [InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_ID}")]
    ]
    await update.message.reply_text("🔥 Welcome", reply_markup=InlineKeyboardMarkup(kb))


# ================= PLANS =================
async def plans(update: Update, context):
    q = update.callback_query
    await q.answer()

    buttons = []
    for p in get_plans():
        buttons.append([InlineKeyboardButton(f"{p[1]} ₹{p[3]}", callback_data=f"plan_{p[0]}")])

    await q.message.reply_text("💎 Choose Plan", reply_markup=InlineKeyboardMarkup(buttons))


# ================= PLAN DETAIL =================
async def plan_detail(update: Update, context):
    q = update.callback_query
    await q.answer()

    pid = int(q.data.split("_")[1])
    p = get_plan(pid)

    text = f"""
📦 {p[1]}
👨‍🏫 Mentor: {p[2]}
💰 Price: ₹{p[3]}
⏳ Validity: {p[4]} days
"""

    kb = [[InlineKeyboardButton("💰 Pay & Send Screenshot", callback_data=f"pay_{pid}")]]
    await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))


# ================= PAY =================
async def pay(update: Update, context):
    q = update.callback_query
    await q.answer()

    pid = int(q.data.split("_")[1])
    user_state[q.from_user.id] = pid

    await q.message.reply_text("📸 Send payment screenshot")


# ================= SCREENSHOT =================
async def photo(update: Update, context):
    u = update.message.from_user

    if u.id not in user_state:
        return

    pid = user_state[u.id]
    p = get_plan(pid)

    await context.bot.send_photo(
        ADMIN_ID,
        update.message.photo[-1].file_id,
        caption=f"""
📩 Payment Request

👤 @{u.username}
🆔 {u.id}
📦 Plan: {p[1]}

Approve:
/approve {u.id} {pid}
"""
    )

    await update.message.reply_text("✅ Sent to admin")


# ================= APPROVE =================
async def approve(update: Update, context):
    uid = int(context.args[0])
    pid = int(context.args[1])

    p = get_plan(pid)

    now = datetime.now()
    exp = now + timedelta(days=p[4])

    add_user(uid, "", "", pid, now.strftime("%Y-%m-%d"), exp.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d"))
    add_payment(uid, pid, p[3])

    link = await context.bot.create_chat_invite_link(
        chat_id=int(p[6]),
        member_limit=1
    )

    await context.bot.send_message(uid, f"✅ Approved\nJoin: {link.invite_link}")


# ================= MY SUB =================
async def my(update: Update, context):
    q = update.callback_query
    await q.answer()

    for u in get_users():
        if u[0] == q.from_user.id:
            p = get_plan(u[3])
            await q.message.reply_text(f"""
📦 Plan: {p[1]}
⏳ Expiry: {u[5]}
""")
            return

    await q.message.reply_text("❌ No active subscription")


# ================= RENEW =================
async def renew(update: Update, context):
    q = update.callback_query
    await q.answer()

    pid = int(q.data.split("_")[1])
    user_state[q.from_user.id] = pid

    await q.message.reply_text("📸 Send screenshot to renew")


# ================= EXPIRY =================
async def expiry(context):
    for u in get_users():
        uid = u[0]
        pid = u[3]
        exp = datetime.strptime(u[5], "%Y-%m-%d")
        now = datetime.now()

        p = get_plan(pid)

        # Reminder
        if exp - now <= timedelta(days=1) and exp > now:
            kb = [[InlineKeyboardButton("🔄 Renew", callback_data=f"renew_{pid}")]]
            await context.bot.send_message(uid, "⚠️ Expiring soon", reply_markup=InlineKeyboardMarkup(kb))

            await context.bot.send_message(ADMIN_ID, f"User {uid} expiring soon")

        # Expired
        if now > exp:
            await context.bot.ban_chat_member(int(p[6]), uid)
            await context.bot.unban_chat_member(int(p[6]), uid)
            remove_user(uid)


# ================= ADMIN =================
async def admin(update: Update, context):
    await update.message.reply_text("""
Admin Commands:
/addplan name mentor price validity demo channel
/deleteplan id
""")


# ================= ADD PLAN =================
async def addplan(update: Update, context):
    name, mentor, price, val, demo, ch = context.args
    add_plan(name, mentor, int(price), int(val), demo, ch)
    await update.message.reply_text("✅ Plan added")


# ================= DELETE PLAN =================
async def deleteplan(update: Update, context):
    delete_plan(int(context.args[0]))
    await update.message.reply_text("❌ Deleted")


# ================= APP =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("addplan", addplan))
app.add_handler(CommandHandler("deleteplan", deleteplan))

app.add_handler(CallbackQueryHandler(plans, pattern="plans"))
app.add_handler(CallbackQueryHandler(plan_detail, pattern="plan_"))
app.add_handler(CallbackQueryHandler(pay, pattern="pay_"))
app.add_handler(CallbackQueryHandler(my, pattern="my"))
app.add_handler(CallbackQueryHandler(renew, pattern="renew_"))

app.add_handler(MessageHandler(filters.PHOTO, photo))

app.job_queue.run_repeating(expiry, interval=3600)

app.run_polling()
