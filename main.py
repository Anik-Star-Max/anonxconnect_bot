import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers import (
    start, stop, next_chat, menu, bonus, profile, rules, handle_message,
    handle_callback, report_user, ban_user, unban_user, stats, broadcast,
    give_vip, give_diamonds, view_complaints, view_user_chats
)
from database import init_database
from config import BOT_TOKEN

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
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
