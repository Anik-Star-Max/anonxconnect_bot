from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime, timedelta
from translation import translate_message
import config
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user = update.effective_user
    db.add_user(user.id, user.full_name)
    
    await update.message.reply_text(
        "🌟 Welcome to Anonymous Chat!\n\n"
        "🔒 Your identity is completely hidden\n"
        "💬 Chat with strangers anonymously\n\n"
        "Use /next to find a chat partner\n"
        "Use /menu for VIP features\n"
        "Use /rules to see community guidelines"
    )

async def next_chat(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or user['banned']:
        await update.message.reply_text("🚫 You are banned from using this bot")
        return
    
    if user['partner']:
        partner_id = user['partner']
        db.update_user(partner_id, partner=None, waiting=True)
        await context.bot.send_message(partner_id, "⚠️ Your partner has disconnected. Use /next to find a new chat.")
    
    db.update_user(user_id, partner=None, waiting=True)
    
    partner_id = db.find_match(user_id)
    if partner_id:
        db.update_user(user_id, partner=partner_id, waiting=False)
        db.update_user(partner_id, partner=user_id, waiting=False)
        await context.bot.send_message(user_id, "✅ You're now connected! Start chatting!")
        await context.bot.send_message(partner_id, "✅ You're now connected! Start chatting!")
    else:
        await update.message.reply_text("🔍 Searching for a partner... We'll notify you when we find one!")

async def stop_chat(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user and user['partner']:
        partner_id = user['partner']
        db.update_user(partner_id, partner=None, waiting=True)
        await context.bot.send_message(partner_id, "⚠️ Your partner has ended the chat. Use /next to find a new partner.")
    
    db.update_user(user_id, partner=None, waiting=False)
    await update.message.reply_text("🛑 Chat ended. Use /next to find a new partner.")

async def menu(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    is_vip = db.is_vip(user_id)
    
    keyboard = []
    if is_vip:
        keyboard.extend([
            [InlineKeyboardButton("🚻 Set Gender Preference", callback_data='set_gender')],
            [InlineKeyboardButton("🎂 Set Age Preference", callback_data='set_age')],
            [InlineKeyboardButton("👤 View My Profile", callback_data='view_profile')]
        ])
    else:
        keyboard.append([InlineKeyboardButton("💎 Get VIP Status", callback_data='vip_purchase')])
    
    keyboard.append([InlineKeyboardButton("📜 Rules", callback_data='rules')])
    
    await update.message.reply_text(
        "📋 Main Menu\n\n" +
        (f"🌟 VIP Status: Active\n💎 Diamonds: {user['vip']['diamonds']}\n\n" if is_vip else "🔓 Unlock VIP Features:\n- Gender filtering\n- Age filtering\n- Profile preview\n\n") +
        "Select an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_message(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or user['banned'] or not user['partner']:
        if update.message.text and not update.message.text.startswith('/'):
            await update.message.reply_text("⚠️ You're not in a chat. Use /next to find a partner.")
        return
    
    partner = db.get_user(user['partner'])
    if not partner or partner['banned'] or partner['partner'] != user_id:
        db.update_user(user_id, partner=None)
        await update.message.reply_text("⚠️ Partner disconnected. Use /next to find a new chat.")
        return
    
    try:
        partner_id = partner['id']
        if update.message.text:
            translated = translate_message(update.message.text, user['language'], partner['language'])
            await context.bot.send_message(partner_id, translated)
        elif update.message.sticker:
            await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
        elif update.message.photo:
            caption = translate_message(update.message.caption or "", user['language'], partner['language'])
            await context.bot.send_photo(partner_id, update.message.photo[-1].file_id, caption=caption)
    except Exception as e:
        logger.error(f"Message failed: {str(e)}")
        db.update_user(user_id, partner=None)
        await update.message.reply_text("⚠️ Message delivery failed. Partner might have left.")

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    db = context.bot_data['db']
    user = db.get_user(user_id)
    
    if data == 'vip_purchase':
        keyboard = [
            [InlineKeyboardButton(f"1 Day - {config.VIP_PRICES[1]} 💎", callback_data='vip_1')],
            [InlineKeyboardButton(f"2 Days - {config.VIP_PRICES[2]} 💎", callback_data='vip_2')],
            [InlineKeyboardButton(f"3 Days - {config.VIP_PRICES[3]} 💎", callback_data='vip_3')],
            [InlineKeyboardButton(f"5 Days - {config.VIP_PRICES[5]} 💎", callback_data='vip_5')],
        ]
        await query.edit_message_text(
            f"💎 VIP Packages:\n\nYour diamonds: {user['vip']['diamonds']}\n\n"
            "1. 1 Day VIP - 500💎\n"
            "2. 2 Days VIP - 1000💎\n"
            "3. 3 Days VIP - 1500💎\n"
            "4. 5 Days VIP - 2000💎\n\n"
            "Select a package:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith('vip_'):
        days = int(data.split('_')[1])
        cost = config.VIP_PRICES[days]
        if user['vip']['diamonds'] >= cost:
            expiry = datetime.now() + timedelta(days=days)
            db.update_user(user_id, vip_expiry=expiry.isoformat(), diamonds=user['vip']['diamonds'] - cost)
            await query.edit_message_text(f"🎉 VIP activated for {days} days!")
        else:
            await query.edit_message_text("❌ Not enough diamonds! Earn more to purchase VIP.")

async def report(update: Update, context: CallbackContext):
    db = context.bot_data['db']
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user or not user['partner']:
        await update.message.reply_text("⚠️ You can only report during an active chat")
        return
    
    reason = ' '.join(context.args)
    if not reason:
        await update.message.reply_text("Please provide a reason: /report [reason]")
        return
    
    # Add complaint to database
    complaint = {
        'from_user': user_id,
        'against_user': user['partner'],
        'reason': reason,
        'timestamp': datetime.now().isoformat()
    }
    if 'complaints' not in db.__dict__:
        db.complaints = {}
    db.complaints[str(datetime.now().timestamp())] = complaint
    
    # Notify admin
    await context.bot.send_message(
        config.ADMIN_ID,
        f"🚨 New Report!\nFrom: {user_id}\nAgainst: {user['partner']}\nReason: {reason}"
    )
    await update.message.reply_text("✅ Your report has been submitted. Admins will review it.")

async def rules(update: Update, context: CallbackContext):
    try:
        with open('rules.txt', 'r') as f:
            rules_text = f.read()
        await update.message.reply_text(f"📜 Community Rules:\n\n{rules_text}")
    except:
        await update.message.reply_text(
            "📜 Community Rules:\n\n"
            "1. No harassment or hate speech\n"
            "2. No sharing personal information\n"
            "3. No spamming\n"
            "4. Respect all users\n"
            "Violations may result in a ban."
        )

def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("rules", rules))
    
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO | filters.Sticker.ALL,
        handle_message
    ))
    
    application.add_handler(CallbackQueryHandler(button_handler))
