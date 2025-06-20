import os
import json
import random
import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
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

# ===== CONFIGURATION =====
TOKEN = os.getenv("TELEGRAM_TOKEN", "8117045817:AAEIWRAV3iDt97-Cu0lMoEAvte1n4i4wNUw")
BOT_NAME = "Anonymous Connect"
VIP_COST = 100  # 💎 required for VIP status

# ===== DATA STORAGE =====
DB_FILE = "users.json"
ACTIVE_CHATS = {}  # {user_id: partner_id}
WAITING_USERS = []  # [user_id1, user_id2, ...]

# Initialize database
def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)

# Load user data
def load_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# Save user data
def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

# Get user data
def get_user(user_id):
    users = load_users()
    return users.get(str(user_id))

# Create/update user
def save_user(user_id, data):
    users = load_users()
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            "created_at": datetime.now().isoformat(),
            "diamonds": 0,
            "vip": False,
            "likes": 0,
            "dislikes": 0,
            "complaints": 0,
            "bonus_points": 0,
            "blacklisted": False
        }
    users[user_id].update(data)
    save_users(users)
    return users[user_id]

# ===== STATES =====
(
    START, PROFILE_PHOTO, PROFILE_GENDER, PROFILE_LANGUAGE, PROFILE_BIO,
    MENU, CHATTING, FEEDBACK, COMPLAINT_TYPE, COMPLAINT_DETAILS,
    VIP_PROFILE_VIEW
) = range(11)

# ===== LANGUAGES =====
LANGUAGES = {
    "en": "English 🇺🇸",
    "hi": "Hindi 🇮🇳",
    "bn": "Bengali 🇧🇩",
    "es": "Spanish 🇪🇸",
    "fr": "French 🇫🇷",
    "de": "German 🇩🇪",
    "ru": "Russian 🇷🇺",
    "zh": "Chinese 🇨🇳",
    "ar": "Arabic 🇸🇦",
    "ja": "Japanese 🇯🇵"
}

# ===== HELPER FUNCTIONS =====
def get_main_menu(user):
    buttons = [
        ["Start Chat 🚀", "Stop Chat ⛔"],
        ["Next Partner ⏭️", "My Profile 👤"],
        ["VIP Access 💎", "Referral Program 🤝"],
        ["Daily Bonus 🎁", "Language 🌐"],
        ["Report User 🛑", "Help ❓"]
    ]
    if user.get("vip"):
        buttons.insert(2, ["VIP Lounge ✨"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_gender_keyboard():
    return ReplyKeyboardMarkup([
        ["Male ♂️", "Female ♀️"],
        ["Other ❔"]
    ], resize_keyboard=True)

def get_language_keyboard():
    keyboard = []
    languages = list(LANGUAGES.items())
    for i in range(0, len(languages), 2):
        row = [f"{name} ({code})" for code, name in languages[i:i+2]]
        keyboard.append(row)
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_feedback_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👍 Like", callback_data="feedback_like"),
            InlineKeyboardButton("👎 Dislike", callback_data="feedback_dislike"),
            InlineKeyboardButton("🛑 Complaint", callback_data="feedback_complaint")
        ]
    ])

def get_complaint_keyboard():
    return ReplyKeyboardMarkup([
        ["Spam or Scam", "Abuse or Hate Speech"],
        ["Sexual Harassment", "Fake Profile"],
        ["Asked for personal info", "Other - Write your own"],
        ["Cancel"]
    ], resize_keyboard=True)

def get_vip_profile_keyboard(partner_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Like Profile", callback_data=f"vip_like_{partner_id}")],
        [InlineKeyboardButton("➖ Dislike Profile", callback_data=f"vip_dislike_{partner_id}")],
        [InlineKeyboardButton("✅ Start Chat", callback_data="vip_start_chat")]
    ])

def get_profile_preview_keyboard(partner_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Like", callback_data=f"like_{partner_id}")],
        [InlineKeyboardButton("➖ Dislike", callback_data=f"dislike_{partner_id}")],
        [InlineKeyboardButton("💎 See VIP Profile", callback_data=f"vip_preview_{partner_id}")]
    ])

# ===== COMMAND HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if user and user.get("photo") and user.get("gender") and user.get("language"):
        await update.message.reply_text(
            f"🌟 *Welcome back to {BOT_NAME}!*\n\n"
            "Your profile is complete. Use /menu to access all features.",
            parse_mode="Markdown",
            reply_markup=get_main_menu(user)
        )
        return MENU
    else:
        await update.message.reply_text(
            f"👋 *Welcome to {BOT_NAME}!*\n\n"
            "Before we start, let's set up your profile.\n"
            "Please upload your display photo (DP).",
            parse_mode="Markdown"
        )
        return PROFILE_PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo_file = await update.message.photo[-1].get_file()
    
    save_user(user_id, {
        "photo": photo_file.file_id,
        "username": update.effective_user.username,
        "first_name": update.effective_user.first_name,
        "last_name": update.effective_user.last_name
    })
    
    await update.message.reply_text(
        "✅ Photo uploaded successfully!\n"
        "Now please select your gender:",
        reply_markup=get_gender_keyboard()
    )
    return PROFILE_GENDER

async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    gender = update.message.text.split()[0].lower()  # "Male ♂️" -> "male"
    
    save_user(user_id, {"gender": gender})
    
    await update.message.reply_text(
        "✅ Gender saved!\n"
        "Now please select your preferred language:",
        reply_markup=get_language_keyboard()
    )
    return PROFILE_LANGUAGE

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    language = update.message.text.split("(")[-1].split(")")[0].strip()  # "English (en)"
    
    if language not in LANGUAGES:
        await update.message.reply_text("Invalid language selection. Please try again.")
        return PROFILE_LANGUAGE
    
    save_user(user_id, {"language": language})
    
    await update.message.reply_text(
        f"✅ Language set to {LANGUAGES[language]}!\n"
        "Would you like to add a short bio? (Optional)\n"
        "Type /skip to proceed without bio."
    )
    return PROFILE_BIO

async def handle_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bio = update.message.text
    save_user(user_id, {"bio": bio})
    
    user = get_user(user_id)
    await update.message.reply_text(
        "🎉 *Profile Complete!*\n\n"
        f"• Gender: {user['gender'].capitalize()}\n"
        f"• Language: {LANGUAGES[user['language']]}\n"
        f"• Bio: {bio}\n\n"
        "You can now use /menu to start chatting!",
        parse_mode="Markdown",
        reply_markup=get_main_menu(user)
    )
    return MENU

async def skip_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    await update.message.reply_text(
        "🎉 *Profile Complete!*\n\n"
        f"• Gender: {user['gender'].capitalize()}\n"
        f"• Language: {LANGUAGES[user['language']]}\n\n"
        "You can now use /menu to start chatting!",
        parse_mode="Markdown",
        reply_markup=get_main_menu(user)
    )
    return MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    await update.message.reply_text(
        "📱 *Main Menu*\n\n"
        "Choose an option:",
        parse_mode="Markdown",
        reply_markup=get_main_menu(user)
    )
    return MENU

async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if user.get("blacklisted"):
        await update.message.reply_text("🚫 You are blacklisted and cannot start chats.")
        return MENU
    
    if user_id in ACTIVE_CHATS:
        await update.message.reply_text("⚠️ You're already in a chat! Use /stop to end current chat first.")
        return MENU
    
    if user_id in WAITING_USERS:
        await update.message.reply_text("🔍 We're already searching for a partner for you...")
        return MENU
    
    # Add to waiting queue
    WAITING_USERS.append(user_id)
    await update.message.reply_text("🔍 Searching for a partner...")
    
    # Try to match immediately
    await try_match(context, user_id)
    
    return MENU

async def try_match(context, user_id):
    if len(WAITING_USERS) < 2:
        return
    
    # Find a partner (simple FIFO matching)
    partner_id = None
    for uid in WAITING_USERS:
        if uid != user_id and uid not in ACTIVE_CHATS:
            partner_id = uid
            break
    
    if not partner_id:
        return
    
    # Remove both from waiting list
    WAITING_USERS.remove(user_id)
    WAITING_USERS.remove(partner_id)
    
    # Create chat connection
    ACTIVE_CHATS[user_id] = partner_id
    ACTIVE_CHATS[partner_id] = user_id
    
    # Get users
    user1 = get_user(user_id)
    user2 = get_user(partner_id)
    
    # Send profile preview to both users
    await context.bot.send_photo(
        chat_id=user_id,
        photo=user2["photo"],
        caption=f"👤 *Partner Found!*\n\n"
                f"💎 Diamonds: {user2.get('diamonds', 0)}\n\n"
                "You can like/dislike their profile before chatting:",
        parse_mode="Markdown",
        reply_markup=get_profile_preview_keyboard(partner_id)
    )
    
    await context.bot.send_photo(
        chat_id=partner_id,
        photo=user1["photo"],
        caption=f"👤 *Partner Found!*\n\n"
                f"💎 Diamonds: {user1.get('diamonds', 0)}\n\n"
                "You can like/dislike their profile before chatting:",
        parse_mode="Markdown",
        reply_markup=get_profile_preview_keyboard(user_id)
    )

async def handle_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    partner_id = int(query.data.split("_")[1])
    
    # Update partner's diamond count
    partner = get_user(partner_id)
    new_diamonds = partner.get("diamonds", 0) + 1
    save_user(partner_id, {"diamonds": new_diamonds})
    
    await query.edit_message_caption(
        caption=f"✅ You liked this profile!\n💎 Diamonds: {new_diamonds}",
        reply_markup=None
    )
    
    # Check if both have liked each other (simplified)
    if ACTIVE_CHATS.get(user_id) == partner_id:
        await start_chat_session(context, user_id, partner_id)

async def handle_dislike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    partner_id = int(query.data.split("_")[1])
    
    # Update partner's dislike count
    partner = get_user(partner_id)
    new_dislikes = partner.get("dislikes", 0) + 1
    save_user(partner_id, {"dislikes": new_dislikes})
    
    await query.edit_message_caption(
        caption="❌ You disliked this profile.",
        reply_markup=None
    )
    
    # End the potential chat
    if user_id in ACTIVE_CHATS:
        del ACTIVE_CHATS[user_id]
    if partner_id in ACTIVE_CHATS:
        del ACTIVE_CHATS[partner_id]
    
    await context.bot.send_message(
        chat_id=user_id,
        text="Chat canceled. Use /menu to try again.",
        reply_markup=get_main_menu(get_user(user_id))
    )

async def start_chat_session(context, user_id, partner_id):
    user1 = get_user(user_id)
    user2 = get_user(partner_id)
    
    # Send start message to both users
    await context.bot.send_message(
        chat_id=user_id,
        text=f"💬 *Chat Started!*\n\n"
             "You can now chat anonymously. Type /stop to end chat.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/stop"]], resize_keyboard=True)
    )
    
    await context.bot.send_message(
        chat_id=partner_id,
        text=f"💬 *Chat Started!*\n\n"
             "You can now chat anonymously. Type /stop to end chat.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["/stop"]], resize_keyboard=True)
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ACTIVE_CHATS:
        await update.message.reply_text("⚠️ You're not in an active chat. Use /menu to start one.")
        return MENU
    
    partner_id = ACTIVE_CHATS[user_id]
    
    if update.message.text:
        await context.bot.send_message(
            chat_id=partner_id,
            text=update.message.text
        )
    elif update.message.photo:
        photo = await update.message.photo[-1].get_file()
        await context.bot.send_photo(
            chat_id=partner_id,
            photo=photo.file_id
        )
    
    return CHATTING

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ACTIVE_CHATS:
        await update.message.reply_text("⚠️ You're not in an active chat.")
        return MENU
    
    partner_id = ACTIVE_CHATS[user_id]
    
    # Remove both from active chats
    del ACTIVE_CHATS[user_id]
    if partner_id in ACTIVE_CHATS:
        del ACTIVE_CHATS[partner_id]
    
    # Send feedback request
    await update.message.reply_text(
        "✅ Chat ended. How was your experience?",
        reply_markup=get_feedback_keyboard()
    )
    
    await context.bot.send_message(
        chat_id=partner_id,
        text="ℹ️ Your partner ended the chat.",
        reply_markup=get_feedback_keyboard()
    )
    
    return FEEDBACK

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    feedback_type = query.data.split("_")[1]
    
    if feedback_type == "like":
        await query.edit_message_text("👍 Thanks for your positive feedback!")
    elif feedback_type == "dislike":
        await query.edit_message_text("👎 We're sorry to hear that. We'll improve!")
    elif feedback_type == "complaint":
        await query.edit_message_text(
            "🛑 Please select the complaint type:",
            reply_markup=get_complaint_keyboard()
        )
        return COMPLAINT_TYPE
    
    # Return to menu
    user = get_user(query.from_user.id)
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text="Returning to main menu...",
        reply_markup=get_main_menu(user)
    )
    return MENU

async def handle_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    complaint_type = update.message.text
    
    if complaint_type == "Cancel":
        user = get_user(update.effective_user.id)
        await update.message.reply_text(
            "Complaint canceled.",
            reply_markup=get_main_menu(user)
        )
        return MENU
    
    context.user_data["complaint_type"] = complaint_type
    
    if "Other" in complaint_type:
        await update.message.reply_text("Please describe the issue:")
        return COMPLAINT_DETAILS
    
    # Save complaint
    save_complaint(update.effective_user.id, complaint_type)
    
    await update.message.reply_text(
        "✅ Complaint submitted. We'll review it shortly.",
        reply_markup=get_main_menu(get_user(update.effective_user.id))
    )
    return MENU

async def handle_complaint_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    details = update.message.text
    complaint_type = context.user_data.get("complaint_type", "Other")
    
    # Save complaint with details
    save_complaint(update.effective_user.id, f"{complaint_type}: {details}")
    
    await update.message.reply_text(
        "✅ Complaint submitted with details. We'll review it shortly.",
        reply_markup=get_main_menu(get_user(update.effective_user.id))
    )
    return MENU

def save_complaint(user_id, complaint):
    user = get_user(user_id)
    complaints = user.get("complaints", 0) + 1
    save_user(user_id, {"complaints": complaints})
    
    # Log complaint
    with open("complaints.log", "a") as f:
        f.write(f"{datetime.now()}: User {user_id} - {complaint}\n")

async def vip_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if user.get("vip"):
        await update.message.reply_text("🌟 You're already a VIP member!")
        return MENU
    
    if user.get("diamonds", 0) >= VIP_COST:
        save_user(user_id, {
            "vip": True,
            "diamonds": user.get("diamonds", 0) - VIP_COST
        })
        await update.message.reply_text(
            "🎉 Congratulations! You're now a VIP member!\n"
            "You now have access to exclusive features.",
            reply_markup=get_main_menu(get_user(user_id))
        )
    else:
        await update.message.reply_text(
            f"⚠️ You need {VIP_COST} 💎 to become a VIP member.\n"
            f"You currently have {user.get('diamonds', 0)} 💎."
        )
    
    return MENU

async def show_vip_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    partner_id = int(query.data.split("_")[-1])
    partner = get_user(partner_id)
    
    caption = (
        f"🌟 *VIP Profile Preview*\n\n"
        f"💎 Diamonds: {partner.get('diamonds', 0)}\n"
        f"👤 Gender: {partner.get('gender', 'Unknown').capitalize()}\n"
        f"🌐 Language: {LANGUAGES.get(partner.get('language', 'en'), 'English')}\n"
        f"📝 Bio: {partner.get('bio', 'No bio provided')}\n\n"
        "Would you like to like/dislike this profile?"
    )
    
    await query.edit_message_caption(
        caption=caption,
        reply_markup=get_vip_profile_keyboard(partner_id)
    )
    return VIP_PROFILE_VIEW

async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    now = datetime.now().isoformat()
    
    last_bonus = user.get("last_bonus")
    if last_bonus and (datetime.now() - datetime.fromisoformat(last_bonus)).days < 1:
        await update.message.reply_text("⏳ You've already claimed your bonus today. Come back tomorrow!")
        return MENU
    
    diamonds = user.get("diamonds", 0) + 5
    save_user(user_id, {
        "diamonds": diamonds,
        "last_bonus": now,
        "bonus_points": user.get("bonus_points", 0) + 1
    })
    
    await update.message.reply_text(
        f"🎁 Daily bonus claimed! +5 💎\n"
        f"Your total diamonds: {diamonds}",
        reply_markup=get_main_menu(get_user(user_id))
    )
    return MENU

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "❓ *Help & Commands*\n\n"
        "• /start - Begin or view your profile\n"
        "• /menu - Main menu\n"
        "• Start Chat - Find an anonymous partner\n"
        "• Stop Chat - End current conversation\n"
        "• Next Partner - Find a new chat partner\n"
        "• VIP Access - Unlock premium features\n"
        "• Referral Program - Earn diamonds\n"
        "• Daily Bonus - Claim free diamonds\n"
        "• Language - Change your language\n"
        "• Report User - Submit a complaint\n\n"
        "💎 VIP Features:\n"
        "- See partner's full profile\n"
        "- View gender and bio\n"
        "- See username after chat\n"
        "- Priority matching\n"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu(get_user(update.effective_user.id))
    )
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    await update.message.reply_text(
        "Operation canceled.",
        reply_markup=get_main_menu(user)
    )
    return MENU

# ===== MAIN APPLICATION =====
def main() -> None:
    # Initialize database
    init_db()
    
    # Set up logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [MessageHandler(filters.TEXT, start)],
            PROFILE_PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
            PROFILE_GENDER: [
                MessageHandler(filters.Regex(r"^(Male|Female|Other)"), handle_gender)
            ],
            PROFILE_LANGUAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_language)
            ],
            PROFILE_BIO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bio),
                CommandHandler("skip", skip_bio)
            ],
            MENU: [
                MessageHandler(filters.Regex(r"^Start Chat 🚀$"), start_chat),
                MessageHandler(filters.Regex(r"^Stop Chat ⛔$"), stop_chat),
                MessageHandler(filters.Regex(r"^Next Partner ⏭️$"), start_chat),
                MessageHandler(filters.Regex(r"^VIP Access 💎$"), vip_access),
                MessageHandler(filters.Regex(r"^Daily Bonus 🎁$"), daily_bonus),
                MessageHandler(filters.Regex(r"^Report User 🛑$"), lambda u, c: handle_feedback(u, c, from_menu=True)),
                MessageHandler(filters.Regex(r"^Help ❓$"), help_command),
                CommandHandler("menu", menu)
            ],
            CHATTING: [
                CommandHandler("stop", stop_chat),
                MessageHandler(filters.TEXT | filters.PHOTO, handle_message)
            ],
            FEEDBACK: [
                CallbackQueryHandler(handle_feedback, pattern=r"^feedback_")
            ],
            COMPLAINT_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complaint)
            ],
            COMPLAINT_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complaint_details)
            ],
            VIP_PROFILE_VIEW: [
                CallbackQueryHandler(handle_like, pattern=r"^vip_like_"),
                CallbackQueryHandler(handle_dislike, pattern=r"^vip_dislike_"),
                CallbackQueryHandler(lambda u, c: start_chat_session(c, u.from_user.id, ACTIVE_CHATS[u.from_user.id]), pattern=r"^vip_start_chat")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Add inline button handlers
    application.add_handler(CallbackQueryHandler(handle_like, pattern=r"^like_"))
    application.add_handler(CallbackQueryHandler(handle_dislike, pattern=r"^dislike_"))
    application.add_handler(CallbackQueryHandler(show_vip_profile, pattern=r"^vip_preview_"))
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
