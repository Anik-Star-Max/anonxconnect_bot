import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers import (
    start,
    stop,
    next_chat,
    menu,
    bonus,
    profile,
    rules,
    referral_top,
    photo_roulette,
    premium,
    get_vip_status,
    translate_status,
    settings,
    report,
    text_message,
    sticker_message,
    photo_message,
    admin_commands,
    error_handler,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # User command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("next", next_chat))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("referral_top", referral_top))
    app.add_handler(CommandHandler("photo_roulette", photo_roulette))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(CommandHandler("get_vip_status", get_vip_status))
    app.add_handler(CommandHandler("translate_status", translate_status))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("report", report))

    # Admin commands (ban, unban, broadcast, assign_vip, stats)
    admin_commands(app)

    # Message handlers for forwarding
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_message))
    app.add_handler(MessageHandler(filters.PHOTO, photo_message))

    app.add_error_handler(error_handler)

    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
