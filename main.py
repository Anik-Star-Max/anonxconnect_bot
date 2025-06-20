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
import os
import logging
import sqlite3
import random
from datetime import datetime, timedelta
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

# Get token from environment variable
TOKEN = os.getenv('TELEGRAM_TOKEN', '8117045817:AAEIWRAV3iDt97-Cu0lMoEAvte1n4i4wNUw')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', '@mysteryman02')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///anonxconnect.db')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
MENU, SET_LANGUAGE, SET_INTERESTS, SET_LOCATION, CHATTING, REPORT_USER, SET_RATING = range(7)

class Database:
    def __init__(self, db_url):
        if db_url.startswith('sqlite:///'):
            self.conn = sqlite3.connect(db_url[10:])
        else:
            # For PostgreSQL or other databases (would need additional setup)
            self.conn = sqlite3.connect('anonxconnect.db')
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language TEXT DEFAULT 'en',
            city TEXT DEFAULT '',
            interests TEXT DEFAULT '',
            rating REAL DEFAULT 5.0,
            rating_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_chats (
            user1_id INTEGER,
            user2_id INTEGER,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user1_id, user2_id)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER,
            reported_id INTEGER,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_bonus (
            user_id INTEGER PRIMARY KEY,
            last_claimed TIMESTAMP
        )
        ''')
        self.conn.commit()

    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

    def create_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) 
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        self.conn.commit()

    def update_user(self, user_id, **fields):
        cursor = self.conn.cursor()
        set_clause = ', '.join([f"{key} = ?" for key in fields])
        values = list(fields.values()) + [user_id]
        cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
        self.conn.commit()

    def create_chat(self, user1_id, user2_id):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO active_chats (user1_id, user2_id) VALUES (?, ?)", (user1_id, user2_id))
        self.conn.commit()

    def delete_chat(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM active_chats WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        self.conn.commit()

    def get_partner(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            CASE 
                WHEN user1_id = ? THEN user2_id 
                ELSE user1_id 
            END AS partner_id
        FROM active_chats 
        WHERE user1_id = ? OR user2_id = ?
        ''', (user_id, user_id, user_id))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_waiting_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        all_users = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT user1_id, user2_id FROM active_chats")
        in_chat_users = set()
        for row in cursor.fetchall():
            in_chat_users.add(row[0])
            in_chat_users.add(row[1])
        
        return [user_id for user_id in all_users if user_id not in in_chat_users]

    def add_complaint(self, reporter_id, reported_id, reason):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO complaints (reporter_id, reported_id, reason) 
        VALUES (?, ?, ?)
        ''', (reporter_id, reported_id, reason))
        self.conn.commit()

    def claim_daily_bonus(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_claimed FROM daily_bonus WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        now = datetime.now()
        can_claim = True
        
        if result:
            last_claimed = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
            if (now - last_claimed) < timedelta(hours=24):
                can_claim = False
        
        if can_claim:
            cursor.execute('''
            INSERT OR REPLACE INTO daily_bonus (user_id, last_claimed) 
            VALUES (?, ?)
            ''', (user_id, now.strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
        
        return can_claim

    def update_rating(self, user_id, rating):
        cursor = self.conn.cursor()
        cursor.execute("SELECT rating, rating_count FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        if result:
            current_rating, count = result
            new_count = count + 1
            new_rating = ((current_rating * count) + rating) / new_count
            cursor.execute("UPDATE users SET rating = ?, rating_count = ? WHERE user_id = ?", 
                          (new_rating, new_count, user_id))
            self.conn.commit()

# Initialize database
db = Database(DATABASE_URL)

# Helper functions
def get_main_menu():
    keyboard = [
        ["Begin Chat 🚀", "Next Chat ⏭️"],
        ["Stop Chat ⛔", "My Profile 👤"],
        ["Daily Bonus 🎁", "Premium 💎"],
        ["Settings ⚙️", "Help ❓"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_settings_menu():
    keyboard = [
        ["Language 🌐", "Interests ❤️"],
        ["Location 📍", "Back ↩️"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_language_options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("English 🇺🇸", callback_data="lang_en")],
        [InlineKeyboardButton("Spanish 🇪🇸", callback_data="lang_es")],
        [InlineKeyboardButton("French 🇫🇷", callback_data="lang_fr")],
        [InlineKeyboardButton("German 🇩🇪", callback_data="lang_de")],
        [InlineKeyboardButton("Russian 🇷🇺", callback_data="lang_ru")]
    ])

def get_rating_options():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1⭐", callback_data="rate_1"),
            InlineKeyboardButton("2⭐", callback_data="rate_2"),
            InlineKeyboardButton("3⭐", callback_data="rate_3"),
            InlineKeyboardButton("4⭐", callback_data="rate_4"),
            InlineKeyboardButton("5⭐", callback_data="rate_5")
        ]
    ])

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.create_user(user.id, user.username, user.first_name, user.last_name)
    
    await update.message.reply_text(
        f"👋 Welcome to Anonymous Chat!\n\n"
        f"• Chat with strangers anonymously\n"
        f"• Find interesting people worldwide\n"
        f"• Share your thoughts freely\n\n"
        f"Press 'Begin Chat 🚀' to start your journey!\n\n"
        f"Bot created by {ADMIN_USERNAME}",
        reply_markup=get_main_menu()
    )
    return MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📱 Main Menu\n\n"
        "Choose an option:",
        reply_markup=get_main_menu()
    )
    return MENU

async def begin_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if db.get_partner(user_id):
        await update.message.reply_text(
            "⚠️ You're already in a chat! Use /stop to end current chat first.",
            reply_markup=get_main_menu()
        )
        return MENU
    
    waiting_users = db.get_waiting_users()
    waiting_users = [uid for uid in waiting_users if uid != user_id]
    
    if not waiting_users:
        await update.message.reply_text(
            "🔍 Searching for a random partner...",
            reply_markup=ReplyKeyboardRemove()
        )
        context.job_queue.run_once(
            callback=retry_search, 
            when=10, 
            data=update.effective_chat.id
        )
        return MENU
    
    partner_id = random.choice(waiting_users)
    db.create_chat(user_id, partner_id)
    
    partner = db.get_user(partner_id)
    interests = partner[6] if partner and len(partner) > 6 else "not set"
    rating = partner[7] if partner and len(partner) > 7 else 5.0
    
    message_text = (
        "🎉 Partner found!\n\n"
        f"• Interests: {interests}\n"
        f"• Rating: {rating:.2f} ⭐\n\n"
        "💬 Start chatting now!\n"
        "/next - Next chat\n"
        "/stop - End chat"
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=message_text,
        reply_markup=ReplyKeyboardMarkup([["/stop", "/next"]], resize_keyboard=True)
    )
    
    await context.bot.send_message(
        chat_id=partner_id,
        text="🎉 You've been connected to a new partner!\n\n"
             "💬 Start chatting now!\n"
             "/next - Next chat\n"
             "/stop - End chat",
        reply_markup=ReplyKeyboardMarkup([["/stop", "/next"]], resize_keyboard=True)
    )
    
    return CHATTING

async def retry_search(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await context.bot.send_message(
        chat_id=chat_id,
        text="😞 No partners available right now. Please try again later.",
        reply_markup=get_main_menu()
    )

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = db.get_partner(user_id)
    
    if partner_id:
        await context.bot.send_message(
            chat_id=partner_id,
            text="ℹ️ Your partner has ended the chat.",
            reply_markup=get_main_menu()
        )
        db.delete_chat(user_id)
    
    await begin_chat(update, context)

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = db.get_partner(user_id)
    
    if partner_id:
        await context.bot.send_message(
            chat_id=partner_id,
            text="ℹ️ Your partner has ended the chat.",
            reply_markup=get_main_menu()
        )
        
        await context.bot.send_message(
            chat_id=partner_id,
            text="Please rate your chat partner:",
            reply_markup=get_rating_options()
        )
    
    db.delete_chat(user_id)
    
    await update.message.reply_text(
        "✅ Chat ended successfully.",
        reply_markup=get_main_menu()
    )
    
    if partner_id:
        await update.message.reply_text(
            "Please rate your chat partner:",
            reply_markup=get_rating_options()
        )
        return SET_RATING
    
    return MENU

async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    rating = int(query.data.split("_")[1])
    
    partner_id = db.get_partner(user_id)
    if partner_id:
        db.update_rating(partner_id, rating)
    
    await query.answer()
    await query.edit_message_text(
        f"⭐ Thanks for your rating! You gave {rating} stars."
    )
    return MENU

async def myprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        username = user[1] or "Not set"
        first_name = user[2] or ""
        last_name = user[3] or ""
        language = user[4] or "Not set"
        city = user[5] or "Not set"
        interests = user[6] or "Not set"
        rating = user[7] or 0.0
        
        await update.message.reply_text(
            "👤 Your Profile\n\n"
            f"• Name: {first_name} {last_name}\n"
            f"• Username: {username}\n"
            f"• Language: {language}\n"
            f"• City: {city}\n"
            f"• Interests: {interests}\n"
            f"• Rating: {rating:.2f} ⭐\n\n"
            "Use /menu to return",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text(
            "Profile not found. Please use /start to create your profile.",
            reply_markup=get_main_menu()
        )
    
    return MENU

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    claimed = db.claim_daily_bonus(user_id)
    
    if claimed:
        await update.message.reply_text(
            "🎁 Daily Bonus Claimed!\n\n"
            "You received 5 extra chat points!\n\n"
            "Come back tomorrow for another bonus!",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text(
            "⏳ You've already claimed your bonus today.\n"
            "Please come back tomorrow!",
            reply_markup=get_main_menu()
        )
    
    return MENU

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 Premium Features\n\n"
        "Upgrade to enjoy exclusive benefits:\n\n"
        "• 🚀 Priority matching\n"
        "• 🌍 Filter partners by location\n"
        "• 🔍 Advanced search filters\n"
        "• 🛡️ Ad-free experience\n"
        "• 💬 Unlimited chat requests\n\n"
        f"Contact {ADMIN_USERNAME} for premium access",
        reply_markup=get_main_menu()
    )
    return MENU

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 Community Guidelines\n\n"
        "1. Respect all users\n"
        "2. No harassment or hate speech\n"
        "3. No explicit content\n"
        "4. No spamming or advertising\n"
        "5. No personal information\n"
        "6. Report inappropriate behavior\n\n"
        "Violations may result in account bans.",
        reply_markup=get_main_menu()
    )
    return MENU

async def complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚠️ Please describe the issue or inappropriate behavior:\n\n"
        "Include details about the user and what happened.",
        reply_markup=ReplyKeyboardMarkup([["Cancel"]], resize_keyboard=True)
    )
    return REPORT_USER

async def handle_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    complaint_text = update.message.text
    
    if complaint_text.lower() == "cancel":
        await update.message.reply_text(
            "Complaint canceled.",
            reply_markup=get_main_menu()
        )
        return MENU
    
    db.add_complaint(user_id, None, complaint_text)
    
    await update.message.reply_text(
        "✅ Your complaint has been submitted.\n"
        "Our moderators will review it shortly.",
        reply_markup=get_main_menu()
    )
    return MENU

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 Select your preferred language:",
        reply_markup=get_language_options()
    )
    return SET_LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang_code = query.data.split("_")[1]
    user_id = query.from_user.id
    
    db.update_user(user_id, language=lang_code)
    
    languages = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ru": "Russian"
    }
    
    await query.answer()
    await query.edit_message_text(
        f"✅ Language set to {languages.get(lang_code, 'English')}"
    )
    return MENU

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ Settings\n\n"
        "Customize your experience:",
        reply_markup=get_settings_menu()
    )
    return SET_LANGUAGE

async def set_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❤️ Enter your interests (comma separated):\n\n"
        "Example: Travel, Music, Technology",
        reply_markup=ReplyKeyboardMarkup([["Cancel"]], resize_keyboard=True)
    )
    return SET_INTERESTS

async def save_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    interests = update.message.text
    
    if interests.lower() == "cancel":
        await update.message.reply_text(
            "Interest update canceled.",
            reply_markup=get_settings_menu()
        )
        return SET_LANGUAGE
    
    db.update_user(user_id, interests=interests)
    
    await update.message.reply_text(
        "✅ Interests updated successfully!",
        reply_markup=get_settings_menu()
    )
    return SET_LANGUAGE

async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📍 Please share your location or type your city:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Share Location", request_location=True)], ["Cancel"]],
            resize_keyboard=True
        )
    )
    return SET_LOCATION

async def save_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if update.message.location:
        city = "From Location"
    else:
        city = update.message.text
        if city.lower() == "cancel":
            await update.message.reply_text(
                "Location update canceled.",
                reply_markup=get_settings_menu()
            )
            return SET_LANGUAGE
    
    db.update_user(user_id, city=city)
    
    await update.message.reply_text(
        f"✅ Location set to: {city}",
        reply_markup=get_settings_menu()
    )
    return SET_LOCATION

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❓ Help & Commands\n\n"
        "• /start - Begin anonymous chat journey\n"
        "• /next - Skip to new conversation\n"
        "• /stop - Finish current conversation\n"
        "• /menu - Access all features\n"
        "• /bonus - Get daily reward\n"
        "• /profile - Manage anonymous identity\n"
        "• /premium - VIP benefits info\n"
        "• /rules - Community guidelines\n"
        "• /myprofile - View rating and details\n"
        "• /complaint - Submit behavior report\n"
        "• /language - Set preferred language\n"
        "• /help - Bot usage instructions\n\n"
        "📱 Use menu buttons for easier navigation!",
        reply_markup=get_main_menu()
    )
    return MENU

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = db.get_partner(user_id)
    
    if partner_id:
        await context.bot.send_message(
            chat_id=partner_id,
            text=update.message.text
        )
        return CHATTING
    
    await update.message.reply_text(
        "⚠️ You're not in a chat. Use 'Begin Chat 🚀' to start.",
        reply_markup=get_main_menu()
    )
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Operation canceled.",
        reply_markup=get_main_menu()
    )
    return MENU

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception: %s", context.error, exc_info=True)
    if update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred. Please try again later.",
            reply_markup=get_main_menu()
        )
    return MENU

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("next", next_chat))
    application.add_handler(CommandHandler("stop", stop_chat))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("bonus", bonus))
    application.add_handler(CommandHandler("profile", myprofile))
    application.add_handler(CommandHandler("premium", premium))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("myprofile", myprofile))
    application.add_handler(CommandHandler("complaint", complaint))
    application.add_handler(CommandHandler("language", language))
    application.add_handler(CommandHandler("help", help_command))
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [
                MessageHandler(filters.Regex(r"^Begin Chat 🚀$"), begin_chat),
                MessageHandler(filters.Regex(r"^Next Chat ⏭️$"), next_chat),
                MessageHandler(filters.Regex(r"^Stop Chat ⛔$"), stop_chat),
                MessageHandler(filters.Regex(r"^My Profile 👤$"), myprofile),
                MessageHandler(filters.Regex(r"^Daily Bonus 🎁$"), bonus),
                MessageHandler(filters.Regex(r"^Premium 💎$"), premium),
                MessageHandler(filters.Regex(r"^Settings ⚙️$"), settings),
                MessageHandler(filters.Regex(r"^Help ❓$"), help_command),
            ],
            SET_LANGUAGE: [
                CallbackQueryHandler(set_language, pattern=r"^lang_"),
                MessageHandler(filters.Regex(r"^Language 🌐$"), language),
                MessageHandler(filters.Regex(r"^Interests ❤️$"), set_interests),
                MessageHandler(filters.Regex(r"^Location 📍$"), set_location),
                MessageHandler(filters.Regex(r"^Back ↩️$"), menu),
            ],
            SET_INTERESTS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_interests),
                MessageHandler(filters.Regex(r"^Cancel$"), cancel),
            ],
            SET_LOCATION: [
                MessageHandler(filters.LOCATION | filters.TEXT, save_location),
                MessageHandler(filters.Regex(r"^Cancel$"), cancel),
            ],
            CHATTING: [
                CommandHandler("next", next_chat),
                CommandHandler("stop", stop_chat),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message),
            ],
            REPORT_USER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complaint),
                MessageHandler(filters.Regex(r"^Cancel$"), cancel),
            ],
            SET_RATING: [
                CallbackQueryHandler(handle_rating, pattern=r"^rate_"),
            ],
        },
        fallbacks=[
            CommandHandler("menu", menu),
            CommandHandler("cancel", cancel),
            CommandHandler("start", start)
        ],
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
