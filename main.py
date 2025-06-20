from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

# ✅ Railway environment se token lena
TOKEN = os.environ.get("BOT_TOKEN")

# ✅ Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *AnonXConnect!*\n\n🔹 Chat anonymously\n🔹 Make new friends\n🔹 No names, just vibes\n\nUse /next to begin chatting, /stop to end.\nType /menu for all commands.",
        parse_mode="Markdown"
    )

# ✅ Next command
async def next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Searching for a new partner...")

# ✅ Stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛑 Your chat has ended. Type /next to start again.")

# ✅ Menu command
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *AnonXConnect Menu:*\n"
        "/start - Begin your anonymous chat journey\n"
        "/next - Skip to a new conversation\n"
        "/stop - Finish your current conversation\n"
        "/bonus - Get your daily reward\n"
        "/profile - Manage your anonymous identity\n"
        "/premium - Learn about VIP benefits\n"
        "/rules - Read community guidelines\n"
        "/myprofile - See your rating and details\n"
        "/complaint - Submit behavior report\n"
        "/language - Set your preferred language\n"
        "/help - Bot usage instructions",
        parse_mode="Markdown"
    )

# ✅ Bonus command
async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎁 Daily reward collected! Come back tomorrow for more.")

# ✅ Profile command
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👤 Profile settings are under development.")

# ✅ Premium command
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 Premium coming soon! Unlock anonymous superpowers.")

# ✅ Rules command
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📜 Rules:\n1. Be respectful\n2. No spam\n3. Keep it clean\n4. Report bad behavior using /complaint")

# ✅ MyProfile command
async def myprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Your Profile:\nUsername: @anonUser\nRating: ⭐️⭐️⭐️⭐️⭐️")

# ✅ Complaint command
async def complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📣 Complaint registered. Our team will take action soon.")

# ✅ Language command
async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌐 Available languages:\n- English\n- Hindi\n- Bengali\n(Feature coming soon)")

# ✅ Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Use /menu to see all commands.\nStart chatting with /start and find partners using /next.")

# ✅ Bot setup
app = ApplicationBuilder().token(TOKEN).build()

# ✅ Command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("next", next))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(CommandHandler("bonus", bonus))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("premium", premium))
app.add_handler(CommandHandler("rules", rules))
app.add_handler(CommandHandler("myprofile", myprofile))
app.add_handler(CommandHandler("complaint", complaint))
app.add_handler(CommandHandler("language", language))
app.add_handler(CommandHandler("help", help_command))

# ✅ Run bot
if __name__ == "__main__":
    app.run_polling()
