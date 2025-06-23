from telegram.ext import Application, CommandHandler, MessageHandler, filters
import handlers, admin, config

def main():
    app = Application.builder().token(config.BOT_TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("next", handlers.next_chat))
    app.add_handler(CommandHandler("stop", handlers.stop_chat))
    app.add_handler(CommandHandler("menu", handlers.menu))
    app.add_handler(CommandHandler("bonus", handlers.daily_bonus))
    app.add_handler(CommandHandler("profile", handlers.profile))
    app.add_handler(CommandHandler("rules", handlers.rules))
    app.add_handler(CommandHandler("referral_top", handlers.referral_top))
    app.add_handler(CommandHandler("photo_roulette", handlers.photo_roulette))
    app.add_handler(CommandHandler("premium", handlers.premium_features))
    app.add_handler(CommandHandler("get_vip_status", handlers.get_vip_status))
    app.add_handler(CommandHandler("translate_status", handlers.translate_status))
    app.add_handler(CommandHandler("settings", handlers.settings))
    app.add_handler(CommandHandler("report", handlers.report))

    # Admin commands
    admin.register_admin_handlers(app)

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message))
    app.add_handler(MessageHandler(filters.PHOTO, handlers.photo_message))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handlers.sticker_message))

    app.add_error_handler(handlers.error_handler)
    print("Bot started.")
    app.run_polling()

if __name__ == "__main__":
    main()
