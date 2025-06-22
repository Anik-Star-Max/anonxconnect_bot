import logging
from telegram.ext import Application, Defaults
from config import BOT_TOKEN
from handlers import register_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def main():
    application = Application.builder().token(BOT_TOKEN).defaults(
        Defaults(parse_mode="HTML")
    ).build()

    register_handlers(application)
    application.run_polling()

if __name__ == "__main__":
    main()
