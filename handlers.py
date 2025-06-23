import os
import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from database import (
    get_user_data, save_user_data, create_user, user_exists,
    get_top_referrals, get_vip_status, set_vip_status, get_complaints,
    set_language, set_photo, set_profile, get_rules, is_admin,
    ban_user, unban_user, broadcast_message, assign_diamonds, get_chat_stats,
    get_all_users, add_referral
)
from translation import translate_message

ADMIN_ID = os.getenv("ADMIN_ID")

# --- User Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user_exists(user.id):
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "gender": None,
            "age": None,
            "vip": False,
            "vip_expiry": None,
            "diamonds": 0,
            "language": "en",
            "current_partner": None,
            "ban": False,
            "is_admin": str(user.id) == str(ADMIN_ID),
            "allow_referral_top": True,
            "photo_url": None,
            "profile": {},
            "settings": {"translate": False}
        }
        create_user(user_data)
    await update.message.reply_text(
        "🆕 Welcome to Anonymous Chat Bot!\n"
        "Type /menu to see options.\n"
        "Your chats are fully anonymous. Enjoy chatting! 🤗"
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Disconnect logic
    await update.message.reply_text("🚫 Chat stopped. Type /next to start a new anonymous chat.")

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Matchmaking logic
    await update.message.reply_text("🔃 Looking for a new chat partner... Please wait.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_keyboard = [
        ["Referral TOP", "Profile"],
        ["Rules", "Photo Roulette"],
        ["Premium", "Get Vip status"],
        ["Translate status", "Settings"]
    ]
    await update.message.reply_text(
        "🔑 Menu / Settings:\nChoose an option below.",
        reply_markup=ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    )

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Daily bonus logic (example, add 50 diamonds)
    user_id = update.effective_user.id
    user = get_user_data(user_id)
    now = datetime.date.today().isoformat()
    last_bonus = user.get("last_bonus", "")
    if last_bonus != now:
        user["diamonds"] = user.get("diamonds", 0) + 50
        user["last_bonus"] = now
        save_user_data(user)
        await update.message.reply_text("⚕️ You received your daily bonus: 50 💎 diamonds!")
    else:
        await update.message.reply_text("You already claimed your daily bonus today. Come back tomorrow!")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_data(update.effective_user.id)
    text = (
        f"👤 Your profile:\n"
        f"Username: {user.get('username')}\n"
        f"Gender: {user.get('gender')}\n"
        f"Age: {user.get('age')}\n"
        f"VIP: {user.get('vip')}\n"
        f"Diamonds: {user.get('diamonds')}\n"
        f"Language: {user.get('language')}\n"
    )
    await update.message.reply_text(text)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_rules())

async def referral_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Show top referrals logic (placeholder)
    await update.message.reply_text("Referral TOP feature coming soon!")

async def photo_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Photo Roulette logic (placeholder)
    await update.message.reply_text("Photo Roulette feature coming soon!")

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 Premium features:\n"
        "- Gender/age match\n"
        "- Profile preview\n"
        "- More diamonds\n"
        "- Photo Roulette likes\n"
        "- Translation power\n"
        "Use /get_vip_status to get VIP!"
    )

async def get_vip_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_data(update.effective_user.id)
    if user.get("vip") == "lifetime":
        await update.message.reply_text("👑 You are a lifetime VIP!")
    elif user.get("vip"):
        await update.message.reply_text(f"🎫 Your VIP expires on: {user.get('vip_expiry')}")
    else:
        await update.message.reply_text("You are not a VIP. Buy VIP with diamonds!")

async def translate_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user_data(update.effective_user.id)
    is_vip = user.get("vip", False)
    if not is_vip:
        await update.message.reply_text("Translation power is for VIP users only.")
        return
    status = user.get("settings", {}).get("translate", False)
    buttons = [["On"], ["Off"]]
    await update.message.reply_text(
        f"Translation is currently {'ON' if status else 'OFF'}.",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ Settings:\nYou can update your profile, language, and other preferences here. (Feature coming soon!)"
    )

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Reporting logic (placeholder)
    await update.message.reply_text("Please describe the issue you want to report:")

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Forwarding logic with translation (placeholder)
    await update.message.reply_text("Forwarded your message to your partner. (Chat system coming soon!)")

async def sticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Forward stickers (placeholder)
    await update.message.reply_text("Sticker forwarded. (Chat system coming soon!)")

async def photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Forward photo logic (placeholder)
    await update.message.reply_text("Photo forwarded. (Chat system coming soon!)")

# --- Admin Handlers ---
def admin_commands(app):
    async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("You are not authorized.")
            return
        if context.args:
            target_id = int(context.args[0])
            ban_user(target_id)
            await update.message.reply_text(f"User {target_id} has been banned.")
        else:
            await update.message.reply_text("Usage: /ban <user_id>")

    async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("You are not authorized.")
            return
        if context.args:
            target_id = int(context.args[0])
            unban_user(target_id)
            await update.message.reply_text(f"User {target_id} has been unbanned.")
        else:
            await update.message.reply_text("Usage: /unban <user_id>")

    async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("You are not authorized.")
            return
        text = " ".join(context.args)
        if text:
            # Implement broadcast logic
            await update.message.reply_text("Broadcast sent. (Feature coming soon!)")
        else:
            await update.message.reply_text("Usage: /broadcast <message>")

    async def assign_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("You are not authorized.")
            return
        if len(context.args) >= 2:
            target_id = int(context.args[0])
            days = int(context.args[1])
            expiry = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
            set_vip_status(target_id, True, expiry)
            await update.message.reply_text(f"User {target_id} assigned VIP for {days} days.")
        else:
            await update.message.reply_text("Usage: /assign_vip <user_id> <days>")

    async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("You are not authorized.")
            return
        stats = get_chat_stats()
        await update.message.reply_text(f"📊 Stats:\nTotal users: {stats['total_users']}\nVIP users: {stats['vip_users']}")

    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("assign_vip", assign_vip))
    app.add_handler(CommandHandler("stats", stats))

async def error_handler(update, context):
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("An error occurred. Please try again later.")
