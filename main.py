import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Import handlers
from handlers import (
    start, stop, next_chat, menu, bonus, profile, rules, handle_message,
    handle_callback, report_user, ban_user, unban_user, stats, broadcast,
    give_vip, give_diamonds, view_complaints, view_user_chats
)

# Import database init & token
from database import init_database
from config import BOT_TOKEN

# Log render environment for debug
admin_id = os.getenv("ADMIN_ID")
bot_username = os.getenv("BOT_USERNAME")

if admin_id is None or bot_username is None:
    logging.warning("ADMIN_ID or BOT_USERNAME is not set in the environment variables.")

print("✅ Render Loaded ADMIN_ID:", admin_id)
print("✅ Render Loaded BOT_USERNAME:", bot_username)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Initialize database
    init_database()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("bonus", bonus))
    application.add_handler(CommandHandler("profile", profile))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("report", report_user))
    
    # Admin commands
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("givevip", give_vip))
    application.add_handler(CommandHandler("givediamonds", give_diamonds))
    application.add_handler(CommandHandler("complaints", view_complaints))
    application.add_handler(CommandHandler("viewchats", view_user_chats))
    
    # Add callback query handler for inline keyboard buttons
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # Add message handler for all non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started successfully!")
    try:
        application.run_polling(allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
