from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackQueryHandler,
    ConversationHandler
)
from datetime import datetime
import config
import database as db
import translation
import referral
import photo_roulette
import admin
import logging

logger = logging.getLogger(__name__)

# Conversation states
SET_LANGUAGE, REPORT_REASON, ADD_PHOTO = range(3)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    
    # Handle referrals
    if context.args and context.args[0].startswith('ref_'):
        referrer_id = int(context.args[0].split('_')[1])
        db.add_referral(referrer_id, user_id)
    
    # Add user
    db.add_user(user_id, user.full_name, config.REFERRAL_BONUS)
    
    await update.message.reply_text(
        "🌟 Welcome to Anonymous Connect!\n\n"
        "🔒 Your identity is completely protected\n"
        "💬 Chat anonymously with strangers\n\n"
        "Your referral link: " + referral.generate_referral_link(user_id) + "\n\n"
        "Use /menu to access all features"
    )

async def menu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = db.get_user(user_id) or {}
    
    keyboard = [
        [InlineKeyboardButton("🏆 Referral TOP", callback_data='referral_top')],
        [InlineKeyboardButton("👤 My Profile", callback_data='profile')],
        [InlineKeyboardButton("📜 Community Rules", callback_data='rules')],
        [InlineKeyboardButton("🎲 Photo Roulette", callback_data='photo_roulette')],
        [InlineKeyboardButton("💎 Premium Features", callback_data='premium')],
        [InlineKeyboardButton("⭐ Get VIP Status", callback_data='get_vip')],
        [InlineKeyboardButton("🌐 Translate Status", callback_data='translate_status')],
        [InlineKeyboardButton("⚙️ Settings", callback_data='settings')]
    ]
    
    # Add admin panel for admin
    if user_id == config.ADMIN_ID:
        keyboard.append([InlineKeyboardButton("👑 Admin Panel", callback_data='admin_panel')])
    
    await update.message.reply_text(
        "📱 Main Menu\n\n"
        "Select an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def referral_top(update: Update, context: CallbackContext):
    top_referrals = db.get_top_referrals()
    text = "🏆 Top Referral Leaders:\n\n"
    
    for i, (user_id, count) in enumerate(top_referrals):
        user = db.get_user(user_id)
        name = user.get('name', f"User {user_id[:4]}") if user else f"User {user_id[:4]}"
        text += f"{i+1}. {name} - {count} referrals\n"
    
    await update.callback_query.edit_message_text(text)

async def profile(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    user = db.get_user(user_id) or {}
    
    vip_status = "Lifetime VIP 👑" if user_id == config.ADMIN_ID else (
        "Active" if db.is_vip(user_id) else "Inactive"
    )
    
    text = (
        "👤 Your Profile\n\n"
        f"Name: {user.get('name', 'Anonymous')}\n"
        f"VIP Status: {vip_status}\n"
        f"Diamonds: {user.get('diamonds', 0)} 💎\n"
        f"Chats Completed: {user.get('chats', 0)}\n"
        f"Rating: {user.get('rating', 0)}/5\n"
        f"Referrals: {user.get('referrals', 0)}\n"
        f"Photos in Roulette: {len(user.get('photos', []))}\n\n"
        "Use /menu to return"
    )
    
    await query.edit_message_text(text)

async def translate_status(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    user = db.get_user(user_id) or {}
    current_status = user.get('translate_enabled', True)
    
    keyboard = [
        [InlineKeyboardButton("✅ ON", callback_data='translate_on')],
        [InlineKeyboardButton("❌ OFF", callback_data='translate_off')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
    ]
    
    status_text = "ENABLED ✅" if current_status else "DISABLED ❌"
    vip_text = "\n\n🌟 VIP Feature" if not db.is_vip(user_id) else ""
    
    text = (
        f"🌐 Translation Status: {status_text}{vip_text}\n\n"
        "Auto-translation converts messages between languages. "
        "Only VIP users can disable translation."
    )
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def get_vip(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    keyboard = []
    for days, price in config.VIP_PRICES.items():
        period = "day" if days == 1 else f"{days} days"
        keyboard.append([InlineKeyboardButton(
            f"⭐ {period} VIP - {price} 💎", 
            callback_data=f'vip_{days}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')])
    
    await query.edit_message_text(
        "💎 VIP Packages\n\n"
        "Unlock premium features:\n"
        "- Disable translation\n"
        "- See who liked your photos\n"
        "- Advanced search filters\n"
        "- Priority matching\n\n"
        "Select a package:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def photo_roulette_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    user = db.get_user(user_id) or {}
    photos = user.get('photos', [])
    
    keyboard = [
        [InlineKeyboardButton("🖼️ Add Photo", callback_data='add_photo')],
        [InlineKeyboardButton("❤️ View My Likes", callback_data='view_likes')],
        [InlineKeyboardButton("🔍 Browse Photos", callback_data='browse_photos')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')]
    ]
    
    text = (
        "🎲 Photo Roulette\n\n"
        f"Your photos: {len(photos)}\n"
        f"Total likes: {sum(photo.get('likes', 0) for photo in photos)}\n"
        f"Earned: {sum(photo.get('likes', 0) * config.PHOTO_LIKE_REWARD} 💎\n\n"
        "Add photos to get likes and earn diamonds)!"
    )
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ... (other handlers) ...

def setup_handlers(application):
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("rules", show_rules))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin.admin_panel))
    application.add_handler(CommandHandler("add_diamonds", admin.add_diamonds))
    application.add_handler(CommandHandler("ban_user", admin.ban_user))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(referral_top, pattern='^referral_top$'))
    application.add_handler(CallbackQueryHandler(profile, pattern='^profile$'))
    application.add_handler(CallbackQueryHandler(translate_status, pattern='^translate_status$'))
    application.add_handler(CallbackQueryHandler(get_vip, pattern='^get_vip$'))
    application.add_handler(CallbackQueryHandler(photo_roulette_menu, pattern='^photo_roulette$'))
    application.add_handler(CallbackQueryHandler(admin.admin_panel, pattern='^admin_panel$'))
    
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Conversation handlers
    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_photo, pattern='^add_photo$')],
        states={
            ADD_PHOTO: [MessageHandler(filters.PHOTO, save_photo)]
        },
        fallbacks=[CommandHandler('cancel', cancel_photo)],
        per_user=True
    ))
