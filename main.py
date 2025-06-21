import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
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
    # Get environment variables
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        return
    
    # Initialize database
    init_database()
    
    # Create the Updater and pass it your bot's token
    updater = Updater(BOT_TOKEN, use_context=True)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("next", next_chat))
    dp.add_handler(CommandHandler("menu", menu))
    dp.add_handler(CommandHandler("bonus", daily_bonus))
    dp.add_handler(CommandHandler("profile", profile))
    dp.add_handler(CommandHandler("rules", rules))
    dp.add_handler(CommandHandler("report", report))
    
    # Admin commands
    dp.add_handler(CommandHandler("ban", ban_user))
    dp.add_handler(CommandHandler("unban", unban_user))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(CommandHandler("broadcast", broadcast))
    dp.add_handler(CommandHandler("givevip", give_vip))
    dp.add_handler(CommandHandler("givediamonds", give_diamonds))
    dp.add_handler(CommandHandler("complaints", view_complaints))
    dp.add_handler(CommandHandler("viewchat", view_user_chat))
    
    # Callback query handler for inline keyboards
    dp.add_handler(CallbackQueryHandler(callback_handler))
    
    # Message handler for chat forwarding
    dp.add_handler(MessageHandler(Filters.text | Filters.sticker | Filters.photo | Filters.video | Filters.voice | Filters.document, handle_message))
    
    # Start the Bot
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
