from telegram.ext import Application
from handlers import setup_handlers
import config
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from database import Database

app = Application.builder().token(config.BOT_TOKEN).build()
setup_handlers(app)
app.run_polling()
# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    db = Database()
    updater = Updater(config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Setup handlers
    setup_handlers(dp)
    
    # Setup periodic tasks
    scheduler = BackgroundScheduler()
    scheduler.add_job(db.cleanup_inactive_users, 'interval', minutes=5)
    scheduler.start()
    
    # Start bot
    updater.start_polling()
    logger.info("Bot started")
    updater.idle()

if __name__ == '__main__':
    main()
