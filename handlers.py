from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)
from datetime import datetime, timedelta
from database import Database
from translation import translate_message
import config
import logging
import re

# Initialize database and logger
db = Database()
logger = logging.getLogger(__name__)

# Conversation states
SET_GENDER, SET_AGE, SET_PREF_GENDER, SET_PREF_AGE = range(4)

# Helper functions
def get_user(update: Update):
    return db.users.get(str(update.effective_user.id))

def update_activity(user_id):
    db.update_user(user_id, last_active=datetime.now().isoformat())

def cleanup_inactive_users():
    now = datetime.now()
    for user_id, user in db.users.items():
        if user['waiting']:
            last_active = datetime.fromisoformat(user['last_active'])
            if (now - last_active).seconds > config.INACTIVITY_TIMEOUT:
                db.update_user(user_id, waiting=False)

# Command handlers
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    db.add_user(user.id, user.full_name)
    
    await update.message.reply_text(
        "🌟 Welcome to Anonymous Chat!\n\n"
        "🔒 Your identity is completely hidden\n"
        "💬 Chat with strangers anonymously\n\n"
        "Use /next to find a chat partner\n"
        "Use /menu for VIP features\n\n"
        "Type /help to see all commands"
    )

async def next_chat(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(update)
    
    if not user or user['banned']:
        await update.message.reply_text("🚫 You are banned from using this bot")
        return
    
    # Disconnect from current partner
    if user['partner']:
        partner_id = user['partner']
        db.update_user(partner_id, partner=None, waiting=True)
        await context.bot.send_message(partner_id, "⚠️ Your partner has disconnected. Use /next to find a new chat.")
    
    db.update_user(user_id, partner=None, waiting=True)
    cleanup_inactive_users()
    
    partner_id = db.find_match(user_id)
    if partner_id:
        # Connect users
        db.update_user(user_id, partner=partner_id, waiting=False)
        db.update_user(partner_id, partner=user_id, waiting=False)
        
        await context.bot.send_message(user_id, "✅ You're now connected to an anonymous partner! Start chatting!")
        await context.bot.send_message(partner_id, "✅ You're now connected to an anonymous partner! Start chatting!")
    else:
        await update.message.reply_text("🔍 Searching for a partner... We'll notify you when we find one!")

async def stop_chat(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(update)
    
    if user and user['partner']:
        partner_id = user['partner']
        db.update_user(partner_id, partner=None, waiting=True)
        await context.bot.send_message(partner_id, "⚠️ Your partner has ended the chat. Use /next to find a new partner.")
    
    db.update_user(user_id, partner=None, waiting=False)
    await update.message.reply_text("🛑 Chat ended. Use /next to find a new partner.")

async def menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(update)
    is_vip = db.is_vip(user_id)
    
    keyboard = []
    if is_vip:
        keyboard.extend([
            [InlineKeyboardButton("🚻 Set Gender Preference", callback_data='set_gender_pref')],
            [InlineKeyboardButton("🎂 Set Age Preference", callback_data='set_age_pref')],
            [InlineKeyboardButton("👤 View My Profile", callback_data='view_profile')]
        ])
    else:
        keyboard.append([InlineKeyboardButton("💎 Get VIP Status", callback_data='vip_purchase')])
    
    keyboard.append([InlineKeyboardButton("📜 View Rules", callback_data='view_rules')])
    
    await update.message.reply_text(
        "📋 Main Menu\n\n" +
        ("🌟 VIP Status: Active\n\n" if is_vip else "🔓 Unlock VIP Features:\n- Gender filtering\n- Age filtering\n- Profile preview\n\n") +
        f"💎 Your diamonds: {user['vip']['diamonds']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def report(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(update)
    
    if not user or not user['partner']:
        await update.message.reply_text("⚠️ You can only report during an active chat")
        return
    
    reason = ' '.join(context.args)
    if not reason:
        await update.message.reply_text("Please provide a reason: /report [reason]")
        return
    
    db.add_complaint(user_id, user['partner'], reason)
    db.update_user(user['partner'], reported_count=user.get('reported_count', 0) + 1)
    
    # Notify admin
    await context.bot.send_message(
        config.ADMIN_ID,
        f"🚨 New Report!\n\nFrom: {user_id}\nAgainst: {user['partner']}\nReason: {reason}"
    )
    
    await update.message.reply_text("✅ Your report has been submitted. Admins will review it shortly.")

# Message handler
async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(update)
    update_activity(user_id)
    
    if not user or user['banned']:
        return
    
    if not user['partner']:
        await update.message.reply_text("⚠️ You're not in a chat. Use /next to find a partner.")
        return
    
    partner_id = user['partner']
    partner = db.users.get(str(partner_id))
    
    if not partner or partner['banned'] or partner['partner'] != user_id:
        db.update_user(user_id, partner=None)
        await update.message.reply_text("⚠️ Partner disconnected. Use /next to find a new chat.")
        return
    
    # Translate message if needed
    partner_lang = partner['language']
    user_lang = user['language']
    
    try:
        if update.message.text:
            translated_text = translate_message(update.message.text, user_lang, partner_lang)
            await context.bot.send_message(partner_id, translated_text)
        elif update.message.sticker:
            await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
        elif update.message.photo:
            caption = update.message.caption
            if caption:
                caption = translate_message(caption, user_lang, partner_lang)
            await context.bot.send_photo(
                partner_id,
                update.message.photo[-1].file_id,
                caption=caption
            )
    except Exception as e:
        logger.error(f"Message forwarding failed: {e}")
        db.update_user(user_id, partner=None)
        await update.message.reply_text("⚠️ Message delivery failed. Partner might have blocked the bot.")

# Admin commands
async def ban_user(update: Update, context: CallbackContext):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /ban <user_id> <reason>")
        return
    
    user_id = context.args[0]
    reason = ' '.join(context.args[1:])
    
    db.update_user(user_id, banned=True)
    await context.bot.send_message(user_id, f"🚫 You've been banned. Reason: {reason}")
    await update.message.reply_text(f"✅ User {user_id} banned successfully.")

# Callback query handlers
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == 'vip_purchase':
        keyboard = [
            [InlineKeyboardButton("1 Day - 500 💎", callback_data='vip_1')],
            [InlineKeyboardButton("2 Days - 1000 💎", callback_data='vip_2')],
            [InlineKeyboardButton("3 Days - 1500 💎", callback_data='vip_3')],
            [InlineKeyboardButton("5 Days - 2000 💎", callback_data='vip_5')],
        ]
        await query.edit_message_text(
            "💎 VIP Packages:\n\n"
            "1. 1 Day - 500 Diamonds\n"
            "2. 2 Days - 1000 Diamonds\n"
            "3. 3 Days - 1500 Diamonds\n"
            "4. 5 Days - 2000 Diamonds\n\n"
            "Select a package:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith('vip_'):
        days = int(data.split('_')[1])
        cost = config.VIP_PRICES[days]
        user = get_user(update)
        
        if user['vip']['diamonds'] >= cost:
            expiry = datetime.now() + timedelta(days=days)
            db.update_user(
                user_id,
                vip_expiry=expiry.isoformat(),
                diamonds=user['vip']['diamonds'] - cost
            )
            await query.edit_message_text(f"🎉 VIP activated for {days} days!")
        else:
            await query.edit_message_text("❌ Not enough diamonds!")

# Setup all handlers
def setup_handlers(application):
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("ban", ban_user))
    
    # Message handler
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Sticker.ALL,
        handle_message
    ))
    
    # Callback query handler
    application.add_handler(CallbackQueryHandler(button_handler))
