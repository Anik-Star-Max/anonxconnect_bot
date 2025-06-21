import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext
)
import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Verify installation
try:
    from telegram import __version__ as ptb_ver
    logger.info(f"✅ Using python-telegram-bot version: {ptb_ver}")
except ImportError as e:
    logger.critical(f"❌ Import error: {str(e)}")
    raise

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🚀 Bot is working! Send /help for commands")

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "✅ Bot is fully functional!\n\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "Try sending a regular message too!"
    )

async def echo(update: Update, context: CallbackContext):
    await update.message.reply_text(f"📨 You said: {update.message.text}")

async def main():
    try:
        application = Application.builder().token(config.BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        logger.info("🚀 Starting bot in polling mode...")
        await application.run_polling()
        
    except Exception as e:
        logger.critical(f"❌ Fatal error: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    asyncio.run(main())
