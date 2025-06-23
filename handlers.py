from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    create_or_update_user, give_daily_bonus, get_profile,
    connect_user, disconnect_user, vip_status, set_translate_status,
    forward_message, get_rules_text
)
from anonxconnect_bot import referral, photo_roulette

MENU_KEYBOARD = [
    ["Referral TOP", "Profile"],
    ["Rules", "Photo Roulette"],
    ["Premium", "Get Vip status"],
    ["Translate status", "Settings"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    create_or_update_user(user.id, user.username)
    await update.message.reply_text(
        "🆕 Welcome to Anonymous Chat Bot!\n"
        "Type /menu to see options.\n"
        "Your chats are fully anonymous. Enjoy chatting! 🤗"
    )

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = connect_user(update.effective_user.id)
    await update.message.reply_text(msg)

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = disconnect_user(update.effective_user.id)
    await update.message.reply_text(msg)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔑 Menu / Settings:\nChoose an option below.",
        reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    )

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = give_daily_bonus(update.effective_user.id)
    await update.message.reply_text(msg)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = get_profile(update.effective_user.id)
    await update.message.reply_text(text)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_rules_text())

async def referral_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(referral.get_referral_top())

async def photo_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(photo_roulette.get_photo_roulette_menu())

async def premium_features(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    msg = vip_status(update.effective_user.id)
    await update.message.reply_text(msg)

async def translate_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg, keyboard = set_translate_status(update.effective_user.id)
    await update.message.reply_text(msg, reply_markup=keyboard)

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Settings: Update profile, language, etc. (Coming soon!)")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please describe the issue you want to report:")

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward_message(update, "text")

async def photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward_message(update, "photo")

async def sticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await forward_message(update, "sticker")

async def error_handler(update, context):
    print(f"Error: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("An error occurred. Please try again later.")
