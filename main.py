from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

# Get the bot token from Railway environment variable
TOKEN = os.environ.get("BOT_TOKEN")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *AnonXConnect!*\n\n🔹 Chat anonymously\n🔹 Make new friends\n🔹 No names, just vibes\n\nType /next to begin, /stop to end.\nLet’s go 🚀",
        parse_mode="Markdown"
    )

# Build bot app
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

# Run the bot
if __name__ == "__main__":
    app.run_polling()


TOKEN = "8117045817:AAEIWRAV3iDt97-Cu0lMoEAvte1n4i4wNUw"
bot = telebot.TeleBot(TOKEN)

user_profiles = {}

@bot.message_handler(commands=['start'])
def start_chat(message):
    bot.send_message(message.chat.id, "Welcome to @anonxconnect_bot! Begin your anonymous chat journey by typing /next.")

@bot.message_handler(commands=['next'])
def next_conversation(message):
    # Logic for starting a new conversation
    bot.send_message(message.chat.id, "You have skipped to a new conversation.")

@bot.message_handler(commands=['stop'])
def stop_conversation(message):
    # Logic for stopping the current conversation
    bot.send_message(message.chat.id, "You have finished your current conversation.")

@bot.message_handler(commands=['menu'])
def access_menu(message):
    bot.send_message(message.chat.id, "Access all features: /bonus, /profile, /premium, /rules, /myprofile, /complaint, /language, /help")

@bot.message_handler(commands=['bonus'])
def daily_reward(message):
    bot.send_message(message.chat.id, "Here is your daily reward!")

@bot.message_handler(commands=['profile'])
def manage_identity(message):
    bot.send_message(message.chat.id, "Manage your anonymous identity.")

@bot.message_handler(commands=['premium'])
def vip_benefits(message):
    bot.send_message(message.chat.id, "Learn about VIP benefits.")

@bot.message_handler(commands=['rules'])
def community_guidelines(message):
    bot.send_message(message.chat.id, "Read community guidelines.")

@bot.message_handler(commands=['myprofile'])
def view_profile(message):
    user_id = message.from_user.id
    profile_info = user_profiles.get(user_id, {"likes": 0, "dislikes": 0})
    bot.send_message(message.chat.id, f"Your profile: Likes: {profile_info['likes']}, Dislikes: {profile_info['dislikes']}")

@bot.message_handler(commands=['complaint'])
def submit_report(message):
    bot.send_message(message.chat.id, "Submit your behavior report.")

@bot.message_handler(commands=['language'])
def set_language(message):
    bot.send_message(message.chat.id, "Set your preferred language.")

@bot.message_handler(commands=['help'])
def bot_usage_instructions(message):
    bot.send_message(message.chat.id, "Bot usage instructions.")

@bot.message_handler(func=lambda message: True)
def handle_feedback(message):
    if message.text == "👍":
        user_id = message.from_user.id
        if user_id not in user_profiles:
            user_profiles[user_id] = {"likes": 0, "dislikes": 0}
        user_profiles[user_id]["likes"] += 1
        bot.send_message(message.chat.id, "Thank you for your feedback!")
    elif message.text == "👎":
        user_id = message.from_user.id
        if user_id not in user_profiles:
            user_profiles[user_id] = {"likes": 0, "dislikes": 0}
        user_profiles[user_id]["dislikes"] += 1
        bot.send_message(message.chat.id, "Thank you for your feedback!")

bot.polling()
