import asyncio
import logging
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import CallbackContext
import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    """Handler for /start command"""
    await update.message.reply_text("🚀 Bot is working! Send /help for commands")

async def help_command(update: Update, context: CallbackContext):
    """Handler for /help command"""
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "Try sending a regular message too!"
    )

async def echo(update: Update, context: CallbackContext):
    """Echo any text message"""
    await update.message.reply_text(f"You said: {update.message.text}")

async def main():
    """Main application function"""
    try:
        # Create application
        application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        # Start polling
        logger.info("Starting bot in polling mode...")
        await application.run_polling()
        
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
