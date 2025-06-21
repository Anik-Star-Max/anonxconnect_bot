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
import signal

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variable to control the application
app = None

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🚀 Bot is working! Send /help for commands")

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "✅ Bot is fully functional!\n"
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message"
    )

async def echo(update: Update, context: CallbackContext):
    await update.message.reply_text(f"📨 You said: {update.message.text}")

async def shutdown():
    """Gracefully shutdown the application"""
    if app:
        logger.info("Starting graceful shutdown...")
        await app.stop()
        await app.shutdown()
        logger.info("Shutdown complete")
        asyncio.get_running_loop().stop()

async def handle_signal(signal_name):
    """Handle OS signals"""
    logger.info(f"Received OS signal: {signal_name}")
    await shutdown()

async def main():
    global app
    try:
        # Create application
        app = Application.builder().token(config.BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        # Register signal handlers
        loop = asyncio.get_running_loop()
        for signame in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(
                signame,
                lambda s=signame: asyncio.create_task(handle_signal(s))
            )
        
        # Start polling
        logger.info("🚀 Starting bot in polling mode...")
        await app.run_polling()
        
    except Exception as e:
        logger.critical(f"❌ Fatal error: {str(e)}", exc_info=True)
    finally:
        logger.info("Bot has stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
