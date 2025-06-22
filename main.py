import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers import *
from database import init_database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Get bot token from environment variables
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    # Initialize database
    init_database()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("next", next_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("bonus", bonus_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("rules", rules_command))
    application.add_handler(CommandHandler("report", report_command))
    
    # Admin commands
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("give_diamonds", give_diamonds_command))
    application.add_handler(CommandHandler("view_chats", view_chats_command))
    
    # Callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Message handler for forwarding messages
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    
    # Run the bot
    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=["message", "callback_query"])

if __name__ == '__main__':
    main()
