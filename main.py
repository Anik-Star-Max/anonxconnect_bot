import asyncio
import logging
from telegram.ext import Application
from handlers import setup_handlers
from database import Database
import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def cleanup_task(db):
    """Periodic cleanup of inactive users"""
    while True:
        await asyncio.sleep(config.INACTIVITY_TIMEOUT)
        count = db.cleanup_inactive_users()
        logger.info(f"Cleaned {count} inactive users")

async def main():
    """Main application function"""
    try:
        # Create database instance
        db = Database()
        
        # Create application
        application = Application.builder().token(config.BOT_TOKEN).build()
        
        # Store database in bot data
        application.bot_data['db'] = db
        
        # Setup handlers
        setup_handlers(application)
        
        # Start cleanup task
        asyncio.create_task(cleanup_task(db))
        
        # Start the bot
        logger.info("Starting bot...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        logger.info("Bot started successfully")
        
        # Run forever
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
    finally:
        logger.info("Bot shutdown")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
