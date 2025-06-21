from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import database as db
import config
import logging

logger = logging.getLogger(__name__)

async def admin_panel(update: Update, context: CallbackContext):
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text("⚠️ Admin access required!")
        return
    
    keyboard = [
        [InlineKeyboardButton("💎 Add Diamonds", callback_data='admin_add_diamonds')],
        [InlineKeyboardButton("🔨 Ban User", callback_data='admin_ban_user')],
        [InlineKeyboardButton("📊 View Stats", callback_data='admin_stats')],
        [InlineKeyboardButton("📢 Send Broadcast", callback_data='admin_broadcast')],
        [InlineKeyboardButton("👀 View User Chats", callback_data='admin_view_chats')]
    ]
    
    await update.message.reply_text(
        "👑 Admin Control Panel\n\n"
        "1. Add diamonds to user accounts\n"
        "2. Ban/unban users\n"
        "3. View system statistics\n"
        "4. Broadcast message to all users\n"
        "5. Monitor user chats\n\n"
        "Select an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_diamonds(update: Update, context: CallbackContext):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    try:
        # Command format: /add_diamonds <user_id> <amount>
        user_id = int(context.args[0])
        amount = int(context.args[1])
        
        user = db.get_user(user_id)
        if user:
            user['diamonds'] = user.get('diamonds', 0) + amount
            db.save_users()
            await update.message.reply_text(f"✅ Added {amount} 💎 to user {user_id}")
        else:
            await update.message.reply_text("❌ User not found")
    except:
        await update.message.reply_text("Usage: /add_diamonds <user_id> <amount>")

async def ban_user(update: Update, context: CallbackContext):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    try:
        # Command format: /ban_user <user_id> <reason>
        user_id = int(context.args[0])
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Violation of terms"
        
        user = db.get_user(user_id)
        if user:
            user['banned'] = True
            db.save_users()
            await context.bot.send_message(user_id, f"🚫 You've been banned. Reason: {reason}")
            await update.message.reply_text(f"✅ Banned user {user_id}")
        else:
            await update.message.reply_text("❌ User not found")
    except:
        await update.message.reply_text("Usage: /ban_user <user_id> <reason>")

async def view_user_chats(update: Update, context: CallbackContext):
    if update.effective_user.id != config.ADMIN_ID:
        return
    
    # This would connect to your chat storage system
    # For simplicity, we'll just show a placeholder
    await update.callback_query.edit_message_text(
        "👀 User Chat Monitoring\n\n"
        "This feature allows admins to view active chats:\n"
        "1. Chat ID: 12345 - UserA & UserB\n"
        "2. Chat ID: 67890 - UserC & UserD\n\n"
        "Select a chat to monitor in real-time"
    )
