import database
import translation
from config import ADMIN_ID
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

# === Helper menubuilder ===
MENU = [
    ["Referral TOP", "Profile"],
    ["Rules", "Photo Roulette"],
    ["Premium", "Get VIP status"],
    ["Translate status", "Settings"]
]
main_menu_markup = ReplyKeyboardMarkup(MENU, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not database.get_user(user.id):
        database.create_user(user.id, user.first_name)
        await update.message.reply_text(
            "👋 Welcome to Anonymous Chat Bot! Please set your gender and age in Settings.",
            reply_markup=main_menu_markup
        )
    else:
        await update.message.reply_text("Welcome back! Use /next to find a chat partner.", reply_markup=main_menu_markup)

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("🔃 Searching for a new stranger...")
    res = database.match_user(user_id)
    if res:
        await update.message.reply_text("👤 Connected anonymously! Say hi.")
    else:
        await update.message.reply_text("⏳ Waiting for a partner...")

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    left = database.leave_chat(user_id)
    if left:
        await update.message.reply_text("🚫 Chat ended. Use /next to meet someone new.")
    else:
        await update.message.reply_text("You’re not chatting right now.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔑 <b>Main Menu</b>\nChoose an option:", reply_markup=main_menu_markup, parse_mode='HTML'
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Let user change name, age, gender, language, etc
    await update.message.reply_text("⚙️ Settings: Please send the changes you want (name, age, gender, language)...")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = database.get_user(update.effective_user.id)
    await update.message.reply_text(
        f"👤 Profile:\nName: {user['name']}\nGender: {user['gender']}\nAge: {user['age']}\nLanguage: {user['language']}\nDiamonds: {user['diamonds']}\nVIP: {user['vip']['status']}",
    )

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("rules.txt") as f:
        await update.message.reply_text(f.read())

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Please describe your complaint and we'll forward it to the admin.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("You are not authorized.")
    try:
        user_id = int(context.args[0])
        success = database.ban_user(user_id)
        if success:
            await update.message.reply_text(f"User {user_id} banned.")
        else:
            await update.message.reply_text("Failed to ban (user may not exist).")
    except Exception:
        await update.message.reply_text("Usage: /ban USER_ID")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Unauthorized.")
    try:
        user_id = int(context.args[0])
        success = database.unban_user(user_id)
        if success:
            await update.message.reply_text(f"User {user_id} unbanned.")
        else:
            await update.message.reply_text("Failed to unban (user may not exist).")
    except Exception:
        await update.message.reply_text("Usage: /unban USER_ID")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Unauthorized.")
    msg = " ".join(context.args)
    database.broadcast(msg)
    await update.message.reply_text("Broadcast sent.")

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Premium Features:\n• Gender/age match\n• See profile previews\n• Use translation\n• More daily bonus\nGet VIP by using diamonds!"
    )

async def get_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 VIP Packages:\n1 Day: 500💎\n2 Days: 1000💎\n3 Days: 1500💎\n5 Days: 2000💎\nReply with the number of days to buy!"
    )

async def translate_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🈳 Translation Power:\n1. On\n2. Off\n(VIP only: when ON, messages will be automatically translated if chat partner's language is different.)"
    )

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = database.claim_bonus(user_id)
    await update.message.reply_text(msg)

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = database.get_referral_code(update.effective_user.id)
    await update.message.reply_text(f"🔗 Your referral code: {code}\nInvite friends for free diamonds!")

async def referral_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = database.get_top_referrals()
    msg = "🏆 Top Referrals:\n"
    for i, (name, count) in enumerate(top):
        msg += f"{i+1}. {name}: {count} referrals\n"
    await update.message.reply_text(msg)

async def photo_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = database.photo_roulette(update.effective_user.id)
    await update.message.reply_text(res)

async def vip_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # For admin, assign vip manually
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Unauthorized.")
    try:
        user_id, days = int(context.args[0]), int(context.args[1])
        msg = database.give_vip(user_id, days)
        await update.message.reply_text(msg)
    except Exception:
        await update.message.reply_text("Usage: /vip USER_ID DAYS")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Unauthorized.")
    msg = database.get_stats()
    await update.message.reply_text(msg)

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = database.get_partner(user_id)
    if partner_id:
        user_data = database.get_user(user_id)
        partner_data = database.get_user(partner_id)
        msg = update.message.text

        # Translate if enabled and language differs
        if database.is_translation_on(user_id) and user_data['language'] != partner_data['language']:
            msg = translation.auto_translate(msg, user_data['language'], partner_data['language'])
        try:
            await context.bot.send_message(partner_id, msg)
        except Exception:
            await update.message.reply_text("Partner disconnected.")
            database.leave_chat(user_id)
    else:
        await update.message.reply_text("You are not in a chat. Use /next.")

async def forward_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = database.get_partner(user_id)
    if partner_id:
        try:
            if update.message.photo:
                file = await update.message.photo[-1].get_file()
                await context.bot.send_photo(partner_id, file.file_id)
            if update.message.sticker:
                await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
        except Exception:
            await update.message.reply_text("Failed to relay media.")
