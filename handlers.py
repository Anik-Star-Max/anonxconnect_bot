from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime, timedelta
from database import Database
from translation import translate_message
import config
import logging
import os

async def start(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    # rest of the function
logger = logging.getLogger(__name__)

def get_user(user_id):
    return db.users.get(str(user_id))

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    db.add_user(user.id, user.full_name)
    text = (
        "🌟 Welcome to Anonymous Chat!\n\n"
        "🔒 Your identity is completely hidden\n"
        "💬 Chat with strangers anonymously\n\n"
        "Use /next to find a chat partner\n"
        "Use /menu for VIP features\n"
        "Use /rules to see community guidelines"
    )
    await update.message.reply_text(text)

async def next_chat(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user['banned']:
        await update.message.reply_text("🚫 You are banned")
        return
    
    if user['partner']:
        partner_id = user['partner']
        db.update_user(partner_id, partner=None, waiting=True)
        await context.bot.send_message(partner_id, "⚠️ Partner disconnected. Use /next")
    
    db.update_user(user_id, partner=None, waiting=True)
    db.cleanup_inactive_users()
    
    partner_id = db.find_match(user_id)
    if partner_id:
        db.update_user(user_id, partner=partner_id, waiting=False)
        db.update_user(partner_id, partner=user_id, waiting=False)
        await context.bot.send_message(user_id, "✅ Connected! Start chatting!")
        await context.bot.send_message(partner_id, "✅ Connected! Start chatting!")
    else:
        await update.message.reply_text("🔍 Searching for a partner...")

async def stop_chat(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if user and user['partner']:
        partner_id = user['partner']
        db.update_user(partner_id, partner=None, waiting=True)
        await context.bot.send_message(partner_id, "⚠️ Chat ended. Use /next")
    db.update_user(user_id, partner=None, waiting=False)
    await update.message.reply_text("🛑 Chat ended. Use /next")

async def menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    is_vip = db.is_vip(user_id)
    
    keyboard = [
        [InlineKeyboardButton("💎 VIP Packages", callback_data='vip_packages')],
        [InlineKeyboardButton("📜 Rules", callback_data='rules')]
    ]
    
    if is_vip:
        keyboard.insert(0, [InlineKeyboardButton("🚻 Gender Preference", callback_data='set_gender')])
        keyboard.insert(1, [InlineKeyboardButton("🎂 Age Preference", callback_data='set_age')])
    
    text = (
        f"📋 Main Menu\n\n"
        f"💎 Diamonds: {user['vip']['diamonds']}\n"
        f"🌟 VIP Status: {'Active' if is_vip else 'Inactive'}\n\n"
        f"{'✨ VIP features unlocked!' if is_vip else '🔓 Unlock VIP for better matching!'}"
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    if not user or user['banned'] or not user['partner']:
        return
    
    partner = get_user(user['partner'])
    if not partner or partner['partner'] != user_id:
        db.update_user(user_id, partner=None)
        await update.message.reply_text("⚠️ Partner disconnected")
        return
    
    try:
        if update.message.text:
            translated = translate_message(
                update.message.text, 
                user['language'], 
                partner['language']
            )
            await context.bot.send_message(partner['id'], translated)
        elif update.message.sticker:
            await context.bot.send_sticker(partner['id'], update.message.sticker.file_id)
        elif update.message.photo:
            caption = translate_message(
                update.message.caption or "", 
                user['language'], 
                partner['language']
            )
            await context.bot.send_photo(
                partner['id'], 
                update.message.photo[-1].file_id,
                caption=caption
            )
    except Exception as e:
        logger.error(f"Forward error: {e}")
        db.update_user(user_id, partner=None)
        await update.message.reply_text("❌ Message failed to send")

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if data == 'vip_packages':
        keyboard = [
            [InlineKeyboardButton(f"1 Day - {config.VIP_PRICES[1]} 💎", callback_data='buy_1')],
            [InlineKeyboardButton(f"2 Days - {config.VIP_PRICES[2]} 💎", callback_data='buy_2')],
            [InlineKeyboardButton(f"3 Days - {config.VIP_PRICES[3]} 💎", callback_data='buy_3')],
            [InlineKeyboardButton(f"5 Days - {config.VIP_PRICES[5]} 💎", callback_data='buy_5')],
        ]
        await query.edit_message_text(
            "💎 VIP Packages:\n\n"
            "1. 1 Day VIP\n"
            "2. 2 Days VIP\n"
            "3. 3 Days VIP\n"
            "4. 5 Days VIP\n\n"
            f"Your diamonds: {user['vip']['diamonds']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith('buy_'):
        days = int(data.split('_')[1])
        cost = config.VIP_PRICES[days]
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

async def report(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or not user['partner']:
        await update.message.reply_text("⚠️ You can only report during a chat")
        return
    
    reason = ' '.join(context.args)
    if not reason:
        await update.message.reply_text("Usage: /report [reason]")
        return
    
    db.add_complaint(user_id, user['partner'], reason)
    db.update_user(user['partner'], reported_count=user.get('reported_count', 0)+1)
    
    await context.bot.send_message(
        config.ADMIN_ID,
        f"🚨 REPORT\nFrom: {user_id}\nAgainst: {user['partner']}\nReason: {reason}"
    )
    await update.message.reply_text("✅ Report submitted to admin")

async def ban_user(update: Update, context: CallbackContext):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /ban <user_id> <reason>")
        return
    
    user_id = context.args[0]
    reason = ' '.join(context.args[1:])
    
    if db.update_user(user_id, banned=True):
        await context.bot.send_message(user_id, f"🚫 You've been banned. Reason: {reason}")
        await update.message.reply_text(f"✅ Banned {user_id}")
    else:
        await update.message.reply_text("❌ User not found")

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("ban", ban_user))
    
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Sticker.ALL,
        handle_message
    ))
    
    application.add_handler(CallbackQueryHandler(button_handler))
