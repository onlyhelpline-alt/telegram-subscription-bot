from telegram import *
from telegram.ext import *
from datetime import datetime, timedelta

from config import *
from database import *

init_db()


# ================= START =================
async def start(update: Update, context):
    kb = [
        [InlineKeyboardButton("💎 Trader VIP Group", callback_data="plans")],
        [InlineKeyboardButton("📊 My Subscription", callback_data="mysub")],
        [InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]
    await update.message.reply_text("🔥 Welcome to VIP Subscription Bot", reply_markup=InlineKeyboardMarkup(kb))


# ================= PLANS =================
async def plans(update, context):
    q = update.callback_query
    await q.answer()

    kb = []
    for p in get_plans():
        key, name, price, *_ = p
        kb.append([InlineKeyboardButton(f"{name} ₹{price}", callback_data=f"plan_{key}")])

    await q.message.reply_text("💎 Choose Your Mentor", reply_markup=InlineKeyboardMarkup(kb))


# ================= PLAN DETAIL =================
async def plan_detail(update, context):
    q = update.callback_query
    await q.answer()

    key = q.data.replace("plan_", "")
    plan = get_plan(key)

    if not plan:
        await q.message.reply_text("❌ Plan not found")
        return

    name, price, validity, demo = plan[1], plan[2], plan[3], plan[4]

    context.user_data["plan"] = key

    kb = [
        [InlineKeyboardButton("💰 Payment Info", callback_data="payinfo")],
        [InlineKeyboardButton("🎬 Check Demo", url=demo)],
        [InlineKeyboardButton("📞 Contact Admin", url=f"https://t.me/{ADMIN_USERNAME}")]
    ]

    await q.message.reply_text(
        f"📦 {name}\n💰 ₹{price}\n⏳ {validity} Days",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= PAYMENT =================
async def payinfo(update, context):
    q = update.callback_query
    await q.answer()

    key = context.user_data["plan"]
    plan = get_plan(key)

    name, price = plan[1], plan[2]

    await context.bot.send_photo(
        chat_id=q.from_user.id,
        photo=open("qr.png", "rb"),
        caption=f"{name}\n₹{price}\nUPI: {UPI_ID}"
    )

    kb = [
        [InlineKeyboardButton("📸 Send Payment Screenshot", callback_data="send_ss")],
        [InlineKeyboardButton("🆔 Send Your Details", callback_data="send_id")]
    ]

    await q.message.reply_text("Choose Option", reply_markup=InlineKeyboardMarkup(kb))


# ================= SEND ID =================
async def send_id(update, context):
    q = update.callback_query
    await q.answer()

    user = q.from_user
    key = context.user_data["plan"]
    plan = get_plan(key)

    name, price = plan[1], plan[2]

    await context.bot.send_message(
        ADMIN_ID,
        f"{user.id} | {name} | ₹{price}"
    )

    await q.message.reply_text("✅ Your Details Sent to admin")


# ================= SCREENSHOT =================
async def send_ss(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["awaiting_ss"] = True
    await q.message.reply_text("📸 Send Payment screenshot")


async def photo(update, context):
    if not context.user_data.get("awaiting_ss"):
        return

    user = update.message.from_user
    key = context.user_data["plan"]
    plan = get_plan(key)

    name, price = plan[1], plan[2]

    kb = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{key}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
    ]]

    await context.bot.send_photo(
        ADMIN_ID,
        update.message.photo[-1].file_id,
        caption=f"{user.id} | {name} | ₹{price}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    await update.message.reply_text("✅ Your Screenshot Received Please wait for admin Approval ✅")


# ================= APPROVE =================
async def approve(update, context):
    q = update.callback_query
    await q.answer()

    data = q.data.replace("approve_", "")
    uid, key = data.split("_", 1)
    uid = int(uid)

    plan = get_plan(key)

    if not plan:
        await q.message.reply_text("❌ Plan not found (Approve)")
        return

    name, price, validity, _, channel = plan[1], plan[2], plan[3], plan[4], plan[5]
    
    now = datetime.now()
    exp = now + timedelta(days=validity)

    user = await context.bot.get_chat(uid)

    add_user(
        uid,
        user.username or "NoUser",
        name,
        price,
        now.strftime("%Y-%m-%d"),
        exp.strftime("%Y-%m-%d")
    )

    link = await context.bot.create_chat_invite_link(
        chat_id=channel,
        member_limit=1
    )

    await context.bot.send_message(
        uid,
        f"🎉 Approved!\n\n📦 {name}\n⏳ {validity} Days\n\n🔗 {link.invite_link}"
    )

    await q.edit_message_reply_markup(None)


# ================= REJECT =================
async def reject(update, context):
    q = update.callback_query
    await q.answer()

    uid = int(q.data.split("_")[1])

    await context.bot.send_message(uid, "❌ Rejected")
    await q.edit_message_reply_markup(None)


# ================= MY SUB =================
async def my(update, context):
    q = update.callback_query
    await q.answer()

    for u in get_users():
        if u[0] == q.from_user.id:
            await q.message.reply_text(f"{u[2]} | Exp: {u[5]}")
            return

    await q.message.reply_text("No subscription")


# ================= ADMIN PANEL =================
async def admin(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return

    kb = [
        [InlineKeyboardButton("📚 Course List", callback_data="course_list")],
        [InlineKeyboardButton("👥 Users", callback_data="total_users")],
        [InlineKeyboardButton("💰 Revenue", callback_data="revenue")],
        [InlineKeyboardButton("📅 Daily Report", callback_data="daily")],
        [InlineKeyboardButton("✏️ Edit Plan", callback_data="edit_plan")],
        [InlineKeyboardButton("❌ Delete Plan", callback_data="delete_plan")],
        [InlineKeyboardButton("➕ Add Plan", callback_data="add_plan")]
    ]

    await update.message.reply_text("⚙️ ADMIN PANEL", reply_markup=InlineKeyboardMarkup(kb))


# ================= ADMIN FEATURES =================
async def course_list(update, context):
    q = update.callback_query
    await q.answer()

    text = "📚 COURSES:\n\n"
    for p in get_plans():
        text += f"{p[0]} | {p[1]} | ₹{p[2]} | {p[3]} Days\n"

    await q.message.reply_text(text)


async def total_users(update, context):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(f"Users: {len(get_users())}")


async def revenue(update, context):
    q = update.callback_query
    await q.answer()
    total = sum([u[3] for u in get_users()])
    await q.message.reply_text(f"Total ₹{total}")


async def daily(update, context):
    q = update.callback_query
    await q.answer()

    today = datetime.now().strftime("%Y-%m-%d")
    total = sum([u[3] for u in get_users() if u[4] == today])

    await q.message.reply_text(f"Today ₹{total}")


# ================= ADD / EDIT / DELETE =================
async def add_plan(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["add"] = True
    await q.message.reply_text("key,name,price,days,demo,channel")


async def edit_plan(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["edit"] = True
    await q.message.reply_text("key,price,days")


async def delete_plan(update, context):
    q = update.callback_query
    await q.answer()
    context.user_data["delete"] = True
    await q.message.reply_text("send key")


async def handle_text(update, context):
    txt = update.message.text

    if context.user_data.get("add"):
        key, name, price, days, demo, channel = txt.split(",")

        add_plan_db(key, name, int(price), int(days), demo, int(channel))

        await update.message.reply_text("✅ Added")
        context.user_data.clear()

    elif context.user_data.get("edit"):
        key, price, days = txt.split(",")

        plan = get_plan(key)
        if plan:
            add_plan_db(
                key,
                plan[1],
                int(price),
                int(days),
                plan[4],
                plan[5]
            )

        await update.message.reply_text("✏️ Updated")
        context.user_data.clear()

    elif context.user_data.get("delete"):
        delete_plan_db(txt.strip())

        await update.message.reply_text("❌ Deleted")
        context.user_data.clear()


# ================= EXPIRY =================
async def expiry(context):
    for u in get_users():
        uid = u[0]
        exp = datetime.strptime(u[5], "%Y-%m-%d")

        if datetime.now() > exp:
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

app.add_handler(CallbackQueryHandler(course_list, pattern="course_list"))
app.add_handler(CallbackQueryHandler(total_users, pattern="total_users"))
app.add_handler(CallbackQueryHandler(revenue, pattern="revenue"))
app.add_handler(CallbackQueryHandler(daily, pattern="daily"))
app.add_handler(CallbackQueryHandler(edit_plan, pattern="edit_plan"))
app.add_handler(CallbackQueryHandler(delete_plan, pattern="delete_plan"))
app.add_handler(CallbackQueryHandler(add_plan, pattern="add_plan"))

app.add_handler(MessageHandler(filters.PHOTO, photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.job_queue.run_repeating(expiry, interval=3600)

app.run_polling()
