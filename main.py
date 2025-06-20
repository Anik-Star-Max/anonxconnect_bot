from telegram.ext import Application
from handlers import setup_handlers
import config
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from database import Database
import asyncio

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def main():
    # Create database instance
    db = Database(config.INACTIVITY_TIMEOUT)
    
    # Create bot application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Store database in bot data for handler access
    application.bot_data['db'] = db
    
    # Setup command and message handlers
    setup_handlers(application)
    
    # Create scheduler for background tasks
    scheduler = BackgroundScheduler()
    
    # Add cleanup job (runs every 5 minutes)
    scheduler.add_job(
        db.cleanup_inactive_users,
        'interval',
        minutes=5,
        max_instances=1
    )
    
    # Start scheduler
    scheduler.start()
    
    # Start the bot
    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    # Run forever until interrupted
    while True:
        await asyncio.sleep(3600)  # Sleep for 1 hour

if __name__ == '__main__':
    # Create event loop
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        if loop.is_running():
            loop.close()
        logger.info("Bot shutdown complete")
