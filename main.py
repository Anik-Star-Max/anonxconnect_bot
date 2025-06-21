
import os
import asyncio
import logging
from telegram.ext import Application
from handlers import setup_handlers
from database import Database

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

async def main():
    """Main application entry point"""
    # Initialize database
    db = Database()
    
    # Create bot application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Store database in bot context
    application.bot_data['db'] = db
    
    # Setup handlers
    setup_handlers(application)
    
    # Start the bot
    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    logger.info("Bot started successfully")
    
    # Run until stopped
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Critical error: {str(e)}")
