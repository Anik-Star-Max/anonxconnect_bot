import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import handlers
from config import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

application = ApplicationBuilder().token(BOT_TOKEN).build()

# Commands
application.add_handler(CommandHandler("start", handlers.start))
application.add_handler(CommandHandler("next", handlers.next_chat))
application.add_handler(CommandHandler("stop", handlers.stop_chat))
application.add_handler(CommandHandler("menu", handlers.menu))
application.add_handler(CommandHandler("bonus", handlers.daily_bonus))
application.add_handler(CommandHandler("profile", handlers.profile))
application.add_handler(CommandHandler("rules", handlers.rules_command))
application.add_handler(CommandHandler("report", handlers.report_command))

# Admin
application.add_handler(CommandHandler("ban", handlers.ban))
application.add_handler(CommandHandler("unban", handlers.unban))
application.add_handler(CommandHandler("broadcast", handlers.broadcast))
application.add_handler(CommandHandler("vip", handlers.vip_admin))
application.add_handler(CommandHandler("stats", handlers.stats))

# Special modules
application.add_handler(CommandHandler("premium", handlers.premium))
application.add_handler(CommandHandler("getvip", handlers.get_vip))
application.add_handler(CommandHandler("translatestatus", handlers.translate_status))
application.add_handler(CommandHandler("settings", handlers.settings))
application.add_handler(CommandHandler("referral", handlers.referral))
application.add_handler(CommandHandler("referraltop", handlers.referral_top))
application.add_handler(CommandHandler("photo_roulette", handlers.photo_roulette))

# Message forwarding for anonymous chat (text, stickers, images)
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handlers.forward_message))
application.add_handler(MessageHandler(filters.PHOTO, handlers.forward_media))
application.add_handler(MessageHandler(filters.STICKER, handlers.forward_media))

if __name__ == '__main__':
    application.run_polling()
