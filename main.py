from telegram.ext import Application
from handlers import setup_handlers
import config
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    db = Database()
    app = Application.builder().token(config.BOT_TOKEN).build()
    
    setup_handlers(app)
    
    # Schedule cleanup job
    scheduler = BackgroundScheduler()
    scheduler.add_job(db.cleanup_inactive_users, 'interval', minutes=5)
    scheduler.start()
    
    app.run_polling()

if __name__ == '__main__':
    main()
