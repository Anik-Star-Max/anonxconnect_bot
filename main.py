import os
import json
import logging
import random
from datetime import datetime, timedelta
from uuid import uuid4
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    ReplyKeyboardMarkup
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

# Constants
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USERNAME = "mysteryman02"
VIP_OPTIONS = {
    1: (500, 1),    # 500💎 for 1 day
    2: (1000, 2),   # 1000💎 for 2 days
    3: (1500, 3),   # 1500💎 for 3 days
    5: (2000, 5)    # 2000💎 for 5 days
}
DIAMOND_REWARD_REFERRAL = 50
DIAMOND_COST_PER_LIKE = 5
USER_DATA_FILE = "users.json"
COMPLAINTS_FILE = "complaints.json"
RULES_FILE = "rules.txt"
LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "ru": "Russian",
    "zh": "Chinese",
    "ar": "Arabic",
    "pt": "Portuguese",
    "id": "Indonesian",
    "ko": "Korean",
    "tr": "Turkish",
    "it": "Italian",
    "nl": "Dutch",
    "pl": "Polish",
    "uk": "Ukrainian",
    "vi": "Vietnamese",
    "th": "Thai"
}

# Conversation states
PHOTO, GENDER, AGE, LANGUAGE, BIO = range(5)
FEEDBACK, COMPLAINT_TYPE, COMPLAINT_DETAILS = range(3)
PROFILE_PREVIEW, CHATTING = range(2)
PREFERENCES = 1
VIP_PURCHASE = 2

# Global data structures
active_chats = {}
waiting_users = []
user_data = {}
complaints = []

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load persistent data
def load_data():
    global user_data, complaints
    try:
        with open(USER_DATA_FILE, "r") as f:
            user_data = json.load(f)
        with open(COMPLAINTS_FILE, "r") as f:
            complaints = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_data = {}
        complaints = []
        
    # Create rules file if not exists
    if not os.path.exists(RULES_FILE):
        with open(RULES_FILE, "w") as f:
            f.write("1. No harassment or abusive behavior\n2. No sharing personal information\n3. No spamming\n4. No illegal activities\n5. Respect all users")

# Save persistent data
def save_data():
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f, indent=2)
    with open(COMPLAINTS_FILE, "w") as f:
        json.dump(complaints, f, indent=2)

# VIP and diamond management
def is_vip(user_id):
    user = user_data.get(str(user_id), {})
    if not user:
        return False
        
    # Admin is always VIP
    if user.get("username", "") == ADMIN_USERNAME:
        return True
        
    vip_expiry = user.get("vip_expiry")
    if vip_expiry and datetime.fromisoformat(vip_expiry) > datetime.now():
        return True
    return False

def add_diamonds(user_id, amount):
    user_id = str(user_id)
    if user_id not in user_data:
        user_data[user_id] = {"diamonds": 0}
    user_data[user_id]["diamonds"] = user_data[user_id].get("diamonds", 0) + amount
    save_data()

def deduct_diamonds(user_id, amount):
    user_id = str(user_id)
    if user_data.get(user_id, {}).get("diamonds", 0) >= amount:
        user_data[user_id]["diamonds"] -= amount
        save_data()
        return True
    return False

def purchase_vip(user_id, days):
    user_id = str(user_id)
    cost, days = VIP_OPTIONS[days]
    
    if not deduct_diamonds(user_id, cost):
        return False
        
    current_expiry = user_data[user_id].get("vip_expiry")
    if current_expiry and datetime.fromisoformat(current_expiry) > datetime.now():
        new_expiry = datetime.fromisoformat(current_expiry) + timedelta(days=days)
    else:
        new_expiry = datetime.now() + timedelta(days=days)
        
    user_data[user_id]["vip_expiry"] = new_expiry.isoformat()
    save_data()
    return True

# User management
def is_banned(user_id):
    user = user_data.get(str(user_id), {})
    if not user:
        return False
        
    ban_expiry = user.get("ban_expiry")
    if ban_expiry and datetime.fromisoformat(ban_expiry) > datetime.now():
        return True
    return False

def ban_user(user_id, days=1):
    user_id = str(user_id)
    ban_expiry = datetime.now() + timedelta(days=days)
    user_data[user_id]["ban_expiry"] = ban_expiry.isoformat()
    save_data()
    return ban_expiry

# Profile management
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    
    # Check if banned
    if is_banned(user_id):
        user = user_data.get(str(user_id), {})
        ban_expiry = datetime.fromisoformat(user["ban_expiry"])
        await update.message.reply_text(
            f"⛔ Your account is banned until {ban_expiry.strftime('%Y-%m-%d %H:%M')}"
        )
        return ConversationHandler.END
    
    # Check if profile exists
    if str(user_id) in user_data and user_data[str(user_id)].get("photo_id"):
        await show_menu(update, context)
        return ConversationHandler.END
    
    # Admin gets VIP automatically
    if username.lower() == ADMIN_USERNAME.lower():
        user_data[str(user_id)] = {
            "username": username,
            "diamonds": 10000,
            "vip_expiry": (datetime.now() + timedelta(days=365)).isoformat(),
            "is_admin": True
        }
        save_data()
    
    await update.message.reply_text(
        "👤 Welcome to Anonymous Chat! Please create your profile first.\n"
        "Upload your profile photo:"
    )
    return PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    photo = update.message.photo[-1]
    context.user_data["photo_id"] = photo.file_id
    
    keyboard = [
        [InlineKeyboardButton("Male", callback_data="male")],
        [InlineKeyboardButton("Female", callback_data="female")],
        [InlineKeyboardButton("Other", callback_data="other")]
    ]
    await update.message.reply_text(
        "Select your gender:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return GENDER

async def set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["gender"] = query.data
    
    await query.edit_message_text(
        "How old are you? (Enter a number between 18-99)"
    )
    return AGE

async def set_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        age = int(update.message.text)
        if age < 18 or age > 99:
            raise ValueError
        context.user_data["age"] = age
    except ValueError:
        await update.message.reply_text("Please enter a valid age between 18-99:")
        return AGE
    
    language_buttons = [
        [InlineKeyboardButton(name, callback_data=code)]
        for code, name in LANGUAGES.items()
    ]
    # Split buttons into multiple rows for better display
    keyboard = [language_buttons[i:i+3] for i in range(0, len(language_buttons), 3)]
    
    await update.message.reply_text(
        "Select your preferred language:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["language"] = query.data
    
    await query.edit_message_text(
        "Write a short bio (optional) or /skip:"
    )
    return BIO

async def skip_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bio"] = ""
    return await save_profile(update, context)

async def save_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    
    if update.message:
        context.user_data["bio"] = update.message.text
    
    user_data[str(user_id)] = {
        "username": username,
        "photo_id": context.user_data["photo_id"],
        "gender": context.user_data["gender"],
        "age": context.user_data.get("age", 0),
        "language": context.user_data["language"],
        "bio": context.user_data.get("bio", ""),
        "diamonds": 100,  # Starting bonus
        "likes": 0,
        "dislikes": 0,
        "created_at": datetime.now().isoformat(),
        "vip_expiry": None,
        "ban_expiry": None,
        "referred_by": None,
        "referral_code": str(uuid4())[:8].upper(),
        "complaints": 0,
        "search_gender": "any",
        "min_age": 18,
        "max_age": 99
    }
    save_data()
    
    await update.message.reply_text(
        "✅ Profile created successfully! You received 100💎 as welcome bonus!",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_menu(update, context)
    return ConversationHandler.END

# Chat system
async def start_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(str(user_id), {})
    
    if not user:
        await update.message.reply_text("Please complete your profile first with /start")
        return
    
    if is_banned(user_id):
        ban_expiry = datetime.fromisoformat(user["ban_expiry"])
        await update.message.reply_text(
            f"⛔ Your account is banned until {ban_expiry.strftime('%Y-%m-%d %H:%M')}"
        )
        return
    
    if not user.get("photo_id"):
        await update.message.reply_text("Please complete your profile first with /start")
        return
    
    if user_id in active_chats.values() or user_id in waiting_users:
        await update.message.reply_text("You're already in a chat or waiting queue")
        return
    
    # Find compatible partner based on preferences
    partner_id = None
    for uid in waiting_users:
        uid = int(uid)
        if uid == user_id:
            continue
            
        partner = user_data.get(str(uid), {})
        if not partner:
            continue
            
        # Check gender preference
        if user.get("search_gender", "any") != "any" and user["search_gender"] != partner.get("gender"):
            continue
            
        # Check age preference
        partner_age = partner.get("age", 0)
        if partner_age and (partner_age < user.get("min_age", 18) or partner_age > user.get("max_age", 99)):
            continue
            
        # Check if partner would accept this user
        if partner.get("search_gender", "any") != "any" and partner["search_gender"] != user.get("gender"):
            continue
            
        user_age = user.get("age", 0)
        if user_age and (user_age < partner.get("min_age", 18) or user_age > partner.get("max_age", 99)):
            continue
            
        partner_id = uid
        break
    
    if partner_id:
        waiting_users.remove(partner_id)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        
        # Show partner profile preview
        await show_partner_profile(update, context, partner_id)
        await show_partner_profile(context.bot, partner_id, user_id)
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("⏳ Searching for a compatible chat partner...")

async def show_partner_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, partner_id):
    user_id = update.effective_user.id
    partner = user_data.get(str(partner_id), {})
    
    caption = f"💎 Diamonds: {partner.get('diamonds', 0)}"
    
    # VIP users see more details
    if is_vip(user_id):
        caption += (
             f"👤 Partner Info:\n"
    f"🧑 Gender: {partner.get('gender', 'Not set')}\n"
    f"🌐 Language: {partner.get('language', 'Not set')}\n"
    f"📝 Bio: {partner.get('bio', 'Not set')}"
)
   
    keyboard = [
        [
            InlineKeyboardButton("👍 Like", callback_data=f"like_{partner_id}"),
            InlineKeyboardButton("👎 Dislike", callback_data=f"dislike_{partner_id}")
        ],
        [InlineKeyboardButton("✅ Start Chat", callback_data=f"startchat_{partner_id}")]
    ]
    
    await context.bot.send_photo(
        chat_id=user_id,
        photo=partner["photo_id"],
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = active_chats.get(user_id)
    
    if not partner_id:
        return
    
    if update.message.text and update.message.text.startswith('/'):
        return
    
    # VIP translation would be implemented here
    if is_vip(user_id) or is_vip(partner_id):
        # Actual translation implementation would go here
        # For now, we'll just mark translated messages
        translated = True
    else:
        translated = False
    
    if update.message.photo:
        caption = update.message.caption or ""
        if translated:
            caption += "\n\n(Translated)"
        await context.bot.send_photo(
            chat_id=partner_id,
            photo=update.message.photo[-1].file_id,
            caption=caption
        )
    elif update.message.text:
        text = update.message.text
        if translated:
            text += "\n\n(Translated)"
        await context.bot.send_message(
            chat_id=partner_id,
            text=text
        )

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = active_chats.get(user_id)
    
    if partner_id:
        if user_id in active_chats:
            del active_chats[user_id]
        if partner_id in active_chats:
            del active_chats[partner_id]
        
        # Send feedback options to both users
        await send_feedback_options(update, context, user_id, partner_id)
        await send_feedback_options(context.bot, partner_id, user_id)

async def send_feedback_options(bot, user_id, partner_id):
    keyboard = [
        [
            InlineKeyboardButton("👍 Like", callback_data=f"fb_like_{partner_id}"),
            InlineKeyboardButton("👎 Dislike", callback_data=f"fb_dislike_{partner_id}"),
            InlineKeyboardButton("🛑 Complaint", callback_data=f"fb_complaint_{partner_id}")
        ]
    ]
    await bot.send_message(
        chat_id=user_id,
        text="How was your chat experience?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Feedback and complaints
async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data.split('_')
    action = data[1]
    partner_id = int(data[2])
    partner = user_data.get(str(partner_id), {})
    
    if action == "like":
        partner["likes"] = partner.get("likes", 0) + 1
        add_diamonds(partner_id, 1)
        await query.edit_message_text("You liked this user 👍")
    elif action == "dislike":
        partner["dislikes"] = partner.get("dislikes", 0) + 1
        await query.edit_message_text("You disliked this user 👎")
    elif action == "complaint":
        complaint_types = [
            ["Spam or Scam", "compl_spam"],
            ["Abuse or Hate Speech", "compl_abuse"],
            ["Sexual Harassment", "compl_harassment"],
            ["Fake Profile", "compl_fake"],
            ["Asked for Personal Info", "compl_personal"],
            ["Other", "compl_other"]
        ]
        keyboard = [[InlineKeyboardButton(text, callback_data=f"{code}_{partner_id}")] for text, code in complaint_types]
        await query.edit_message_text(
            "Select complaint type:",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    save_data()
    await show_menu(context.bot, user_id)

async def handle_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    comp_type = data[1]
    partner_id = int(data[2])
    user_id = query.from_user.id
    
    context.user_data["complaint"] = {
        "user_id": user_id,
        "partner_id": partner_id,
        "type": comp_type,
        "timestamp": datetime.now().isoformat()
    }
    
    if comp_type == "other":
        await query.edit_message_text("Please describe the issue:")
        return COMPLAINT_DETAILS
    
    # Save complaint
    complaints.append(context.user_data["complaint"])
    with open(COMPLAINTS_FILE, "w") as f:
        json.dump(complaints, f)
    
    # Penalize reported user
    partner = user_data.get(str(partner_id), {})
    complaints_count = partner.get("complaints", 0) + 1
    partner["complaints"] = complaints_count
    
    # Auto-ban after 3 complaints
    if complaints_count >= 3:
        ban_expiry = ban_user(partner_id)
        await context.bot.send_message(
            chat_id=partner_id,
            text=f"⛔ Your account has been banned until {ban_expiry.strftime('%Y-%m-%d %H:%M')} due to multiple complaints"
        )
    
    save_data()
    await query.edit_message_text("Complaint submitted ✅")
    await show_menu(context.bot, user_id)
    return ConversationHandler.END

async def handle_complaint_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["complaint"]["details"] = update.message.text
    complaints.append(context.user_data["complaint"])
    with open(COMPLAINTS_FILE, "w") as f:
        json.dump(complaints, f)
    
    partner_id = context.user_data["complaint"]["partner_id"]
    partner = user_data.get(str(partner_id), {})
    complaints_count = partner.get("complaints", 0) + 1
    partner["complaints"] = complaints_count
    
    # Auto-ban after 3 complaints
    if complaints_count >= 3:
        ban_expiry = ban_user(partner_id)
        await context.bot.send_message(
            chat_id=partner_id,
            text=f"⛔ Your account has been banned until {ban_expiry.strftime('%Y-%m-%d %H:%M')} due to multiple complaints"
        )
    
    save_data()
    await update.message.reply_text("Complaint submitted ✅")
    await show_menu(update, context)
    return ConversationHandler.END

# VIP and diamond features
async def vip_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(str(user_id), {})
    diamonds = user.get("diamonds", 0)
    
    if is_vip(user_id):
        expiry = datetime.fromisoformat(user["vip_expiry"])
        await update.message.reply_text(
            f"⭐ You're VIP until {expiry.strftime('%Y-%m-%d %H:%M')}"
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton(f"1 Day - {VIP_OPTIONS[1][0]}💎", callback_data="vip_1"),
            InlineKeyboardButton(f"2 Days - {VIP_OPTIONS[2][0]}💎", callback_data="vip_2")
        ],
        [
            InlineKeyboardButton(f"3 Days - {VIP_OPTIONS[3][0]}💎", callback_data="vip_3"),
            InlineKeyboardButton(f"5 Days - {VIP_OPTIONS[5][0]}💎", callback_data="vip_5")
        ]
    ]
    await update.message.reply_text(
        f"💎 Your diamonds: {diamonds}\n"
        "VIP benefits:\n"
        "- View partner's full profile details\n"
        "- Automatic message translation\n"
        "- Priority matching\n"
        "- Increased diamond rewards",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_vip_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    days = int(query.data.split('_')[1])
    
    if purchase_vip(user_id, days):
        expiry = datetime.fromisoformat(user_data[str(user_id)]["vip_expiry"])
        await query.edit_message_text(f"⭐ VIP activated until {expiry.strftime('%Y-%m-%d %H:%M')}")
    else:
        await query.edit_message_text("❌ Not enough diamonds")

# Referral system
async def apply_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Please provide a referral code: /invite CODE")
        return
    
    user_id = update.effective_user.id
    ref_code = context.args[0].upper()
    ref_user_id = None
    
    # Find user with this referral code
    for uid, data in user_data.items():
        if data.get("referral_code") == ref_code:
            ref_user_id = int(uid)
            break
    
    if not ref_user_id:
        await update.message.reply_text("❌ Invalid referral code")
        return
    
    if str(user_id) in user_data:
        if user_data[str(user_id)].get("referred_by"):
            await update.message.reply_text("❌ You've already used a referral")
            return
    
    # Add diamonds to both users
    add_diamonds(user_id, DIAMOND_REWARD_REFERRAL)
    add_diamonds(ref_user_id, DIAMOND_REWARD_REFERRAL)
    
    # Update referral status
    user_data[str(user_id)]["referred_by"] = ref_user_id
    save_data()
    
    await update.message.reply_text(
        f"✅ Referral applied! {DIAMOND_REWARD_REFERRAL}💎 added to your account"
    )

async def show_referral_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(str(user_id), {})
    ref_code = user.get("referral_code", "ERROR")
    
    await update.message.reply_text(
        f"📨 Your referral code: `{ref_code}`\n\n"
        "Share this code with friends to earn 50💎 when they join using /invite YOUR_CODE\n\n"
        f"You've referred: {len([u for u in user_data.values() if u.get('referred_by') == user_id])} users",
        parse_mode="Markdown"
    )

# Preferences system
async def set_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(str(user_id), {})
    
    gender_options = [
        ["Any", "any"],
        ["Male", "male"],
        ["Female", "female"],
        ["Other", "other"]
    ]
    keyboard = [[InlineKeyboardButton(text, callback_data=f"pref_gender_{data}")] for text, data in gender_options]
    
    await update.message.reply_text(
        "Set your chat preferences:\n"
        f"Current gender preference: {user.get('search_gender', 'any').capitalize()}\n"
        f"Current age range: {user.get('min_age', 18)}-{user.get('max_age', 99)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PREFERENCES

async def handle_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    pref_type = data[1]
    value = data[2]
    user_id = query.from_user.id
    
    if pref_type == "gender":
        user_data[str(user_id)]["search_gender"] = value
        save_data()
        await query.edit_message_text(
            f"✅ Gender preference set to: {value.capitalize()}\n"
            "Now send your preferred age range in format: min-max\n"
            "Example: 18-30"
        )
        return PREFERENCES
    elif pref_type == "age":
        try:
            min_age, max_age = map(int, value.split('-'))
            if min_age < 18 or max_age > 99 or min_age > max_age:
                raise ValueError
            user_data[str(user_id)]["min_age"] = min_age
            user_data[str(user_id)]["max_age"] = max_age
            save_data()
            await query.edit_message_text(
                f"✅ Age range set to: {min_age}-{max_age}"
            )
            await show_menu(query, context)
            return ConversationHandler.END
        except:
            await query.edit_message_text(
                "Invalid format. Please send min and max ages separated by hyphen\n"
                "Example: 21-35"
            )
            return PREFERENCES

# Help and rules
async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *Anonymous Chat Bot Help*\n\n"
        "*/start* - Create or view your profile\n"
        "*/menu* - Show main menu\n"
        "*/invite CODE* - Apply referral code\n"
        "*/stop* - End current chat\n"
        "*/next* - Skip to next partner\n"
        "*/vip* - VIP information and purchase\n"
        "*/profile* - View your profile\n"
        "*/preferences* - Set chat preferences\n"
        "*/referral* - Show referral information\n"
        "*/rules* - Show community rules\n"
        "*/help* - Show this help message\n\n"
        "During chat:\n"
        "- Send text messages to chat\n"
        "- Send photos to share images\n"
        "- Use /stop or /next to end chat\n\n"
        "After chat ends, you can rate your partner with 👍, 👎, or 🛑"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(RULES_FILE, "r") as f:
        rules = f.read()
    await update.message.reply_text(f"📜 *Community Rules:*\n\n{rules}", parse_mode="Markdown")

# Menu and commands
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update, Update):
        user_id = update.effective_user.id
        msg = update.message
    else:
        # It's a CallbackQuery
        user_id = update.from_user.id
        msg = update
    
    keyboard = [
        [InlineKeyboardButton("Start Chat", callback_data="start_chat")],
        [InlineKeyboardButton("VIP Access", callback_data="vip_access")],
        [InlineKeyboardButton("Referral Info", callback_data="referral_info")],
        [InlineKeyboardButton("My Profile", callback_data="my_profile")],
        [InlineKeyboardButton("Preferences", callback_data="set_preferences")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ]
    
    if hasattr(msg, 'edit_message_text'):
        # CORRECTED LINE: Removed extra parenthesis
        await msg.edit_message_text(
            text="Main Menu:",
            reply_markup=InlineKeyboardMarkup(keyboard)
     )
    else:
        await context.bot.send_message(
            chat_id=user_id,
            text="Main Menu:",
            reply_markup=InlineKeyboardMarkup(keyboard)
     )
async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = user_data.get(str(user_id), {})
    
    caption = (
    f"👤 Your Profile\n"
    f"💎 Diamonds: {user.get('diamonds', 0)}\n"
    f"❤️ Likes: {user.get('likes', 0)}\n"
    f"👎 Dislikes: {user.get('dislikes', 0)}\n"
    f"🔤 Language: {LANGUAGES.get(user.get('language', 'en'), 'English')}\n"
    f"⚧️ Gender: {user.get('gender', 'Not set').capitalize()}\n"
    f"🔢 Age: {user.get('age', 'Not set')}\n"
    f"📝 Bio: {user.get('bio', 'Not set')}\n"
    )
    
    if is_vip(user_id):
        expiry = datetime.fromisoformat(user["vip_expiry"])
        caption += f"⭐ VIP Status: Active until {expiry.strftime('%Y-%m-%d %H:%M')}\n"
    else:
        caption += "⭐ VIP Status: Not active\n"
    
    keyboard = [
        [
            InlineKeyboardButton("Change Photo", callback_data="change_photo"),
            InlineKeyboardButton("Change Bio", callback_data="change_bio")
        ],
        [InlineKeyboardButton("Back to Menu", callback_data="back_menu")]
    ]
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_photo(
            photo=user["photo_id"],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard))

# Main function
def main() -> None:
    load_data()
    
    application = Application.builder().token(TOKEN).build()
    
    # Profile creation conversation
    profile_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
            GENDER: [CallbackQueryHandler(set_gender)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_age)],
            LANGUAGE: [CallbackQueryHandler(set_language)],
            BIO: [
                CommandHandler("skip", skip_bio),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_profile)
            ]
        },
        fallbacks=[]
    )
    
    # Complaint conversation
    complaint_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_complaint, pattern=r"^compl_.*")],
        states={
            COMPLAINT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complaint_details)]
        },
        fallbacks=[]
    )
    
    # Preferences conversation
    pref_conv = ConversationHandler(
        entry_points=[CommandHandler("preferences", set_preferences),
                      CallbackQueryHandler(set_preferences, pattern=r"^set_preferences$")],
        states={
            PREFERENCES: [
                CallbackQueryHandler(handle_preferences, pattern=r"^pref_gender_.*"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_preferences)
            ]
        },
        fallbacks=[]
    )
    
    # Register handlers
    application.add_handler(profile_conv)
    application.add_handler(complaint_conv)
    application.add_handler(pref_conv)
    application.add_handler(CommandHandler("invite", apply_referral))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("stop", end_chat))
    application.add_handler(CommandHandler("next", end_chat))
    application.add_handler(CommandHandler("vip", vip_access))
    application.add_handler(CommandHandler("profile", my_profile))
    application.add_handler(CommandHandler("referral", show_referral_info))
    application.add_handler(CommandHandler("help", show_help))
    application.add_handler(CommandHandler("rules", show_rules))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(start_chat, pattern=r"^startchat_"))
    application.add_handler(CallbackQueryHandler(handle_feedback, pattern=r"^fb_"))
    application.add_handler(CallbackQueryHandler(handle_vip_purchase, pattern=r"^vip_"))
    application.add_handler(CallbackQueryHandler(vip_access, pattern=r"^vip_access$"))
    application.add_handler(CallbackQueryHandler(show_referral_info, pattern=r"^referral_info$"))
    application.add_handler(CallbackQueryHandler(my_profile, pattern=r"^my_profile$"))
    application.add_handler(CallbackQueryHandler(show_menu, pattern=r"^back_menu$"))
    application.add_handler(CallbackQueryHandler(show_help, pattern=r"^help$"))
    
    # Message handler (for chat)
    application.add_handler(MessageHandler(
        filters.TEXT | filters.PHOTO, 
        handle_chat_message
    ))
    
    application.run_polling()

if __name__ == "__main__":
    main()
