import json
import random
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext
from database import *
from translation import translate_message, get_user_language
from config import ADMIN_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Anonymous"
    
    # Check if user is banned
    if is_user_banned(user_id):
        update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    # Add user to database
    add_user(user_id, username)
    
    welcome_text = """
🎉 Welcome to Anonymous Chat Bot! 🎉

🌟 Connect with strangers anonymously
🔒 Your identity stays hidden
🌍 Chat with people worldwide
💎 Earn diamonds and unlock VIP features

📋 Available Commands:
/start - 🆕 Start chat
/next - 🔃 Next chat
/stop - 🚫 Stop chat
/menu - 🔑 Menu/Settings
/bonus - ⚕️ Daily bonus
/profile - 👤 Profile
/rules - 💡 Terms of use

Ready to start your anonymous adventure? 🚀
Use /next to find someone to chat with!
"""
    
    update.message.reply_text(welcome_text)

def next_command(update: Update, context: CallbackContext):
    """Handle /next command - find a chat partner"""
    user_id = update.effective_user.id
    
    if is_user_banned(user_id):
        update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    if not user_exists(user_id):
        update.message.reply_text("❌ Please use /start first!")
        return
    
    # Stop current chat if exists
    current_partner = get_user_partner(user_id)
    if current_partner:
        stop_chat(user_id, current_partner)
        context.bot.send_message(current_partner, "💔 Your partner left the chat. Use /next to find someone new!")
    
    # Find a new partner
    partner_id = find_partner(user_id)
    
    if partner_id:
        # Connect users
        set_user_partner(user_id, partner_id)
        set_user_partner(partner_id, user_id)
        
        update.message.reply_text("✅ Connected! You can now chat anonymously. Use /stop to end the chat.")
        context.bot.send_message(partner_id, "✅ Connected! You can now chat anonymously. Use /stop to end the chat.")
    else:
        set_user_waiting(user_id, True)
        update.message.reply_text("⏳ Searching for someone to chat with... Please wait!")

def stop_command(update: Update, context: CallbackContext):
    """Handle /stop command"""
    user_id = update.effective_user.id
    partner_id = get_user_partner(user_id)
    
    if partner_id:
        stop_chat(user_id, partner_id)
        update.message.reply_text("💔 Chat ended. Use /next to find someone new!")
        context.bot.send_message(partner_id, "💔 Your partner left the chat. Use /next to find someone new!")
    else:
        set_user_waiting(user_id, False)
        update.message.reply_text("❌ You're not in a chat right now.")

def menu_command(update: Update, context: CallbackContext):
    """Handle /menu command"""
    user_id = update.effective_user.id
    
    if not user_exists(user_id):
        update.message.reply_text("❌ Please use /start first!")
        return
    
    keyboard = [
        [InlineKeyboardButton("🏆 Referral TOP", callback_data="referral_top"),
         InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("💡 Rules", callback_data="rules"),
         InlineKeyboardButton("📸 Photo Roulette", callback_data="photo_roulette")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium"),
         InlineKeyboardButton("🌟 Get VIP Status", callback_data="get_vip")],
        [InlineKeyboardButton("🌐 Translate Status", callback_data="translate_status"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🔑 **Main Menu**\nChoose an option:", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

def bonus_command(update: Update, context: CallbackContext):
    """Handle /bonus command - daily bonus"""
    user_id = update.effective_user.id
    
    if not user_exists(user_id):
        update.message.reply_text("❌ Please use /start first!")
        return
    
    last_bonus = get_user_last_bonus(user_id)
    today = datetime.now().date()
    
    if last_bonus and last_bonus == today:
        update.message.reply_text("⏰ You've already claimed your daily bonus today! Come back tomorrow.")
        return
    
    # Give daily bonus
    bonus_amount = random.randint(10, 50)
    add_user_diamonds(user_id, bonus_amount)
    set_user_last_bonus(user_id, today)
    
    update.message.reply_text(f"🎁 Daily bonus claimed! You received {bonus_amount} 💎 diamonds!")

def profile_command(update: Update, context: CallbackContext):
    """Handle /profile command"""
    user_id = update.effective_user.id
    
    if not user_exists(user_id):
        update.message.reply_text("❌ Please use /start first!")
        return
    
    user_data = get_user_data(user_id)
    diamonds = user_data.get('diamonds', 0)
    vip_status = "✅ Active" if is_user_vip(user_id) else "❌ Inactive"
    vip_days = get_user_vip_days(user_id)
    gender = user_data.get('gender', 'Not set')
    age = user_data.get('age', 'Not set')
    language = user_data.get('language', 'en')
    referrals = user_data.get('referrals', 0)
    
    profile_text = f"""
👤 **Your Profile**

💎 Diamonds: {diamonds}
🌟 VIP Status: {vip_status}
⏰ VIP Days Left: {vip_days}
👥 Gender: {gender}
🎂 Age: {age}
🌐 Language: {language}
🔗 Referrals: {referrals}
"""
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Profile", callback_data="edit_profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

def rules_command(update: Update, context: CallbackContext):
    """Handle /rules command"""
    try:
        with open('rules.txt', 'r', encoding='utf-8') as f:
            rules_text = f.read()
        update.message.reply_text(f"💡 **Terms of Use**\n\n{rules_text}", parse_mode=ParseMode.MARKDOWN)
    except FileNotFoundError:
        default_rules = """
💡 **Terms of Use**

1. 🚫 No spam, harassment, or abuse
2. 🔞 No adult content or inappropriate behavior
3. 🤝 Be respectful to other users
4. 📷 No sharing personal information
5. 🚨 Report violations using /report
6. 💎 VIP features require diamonds
7. 🔄 Follow community guidelines
8. ⚖️ Admin decisions are final

Violation of these rules may result in a permanent ban.
"""
        update.message.reply_text(default_rules, parse_mode=ParseMode.MARKDOWN)

def report_command(update: Update, context: CallbackContext):
    """Handle /report command"""
    user_id = update.effective_user.id
    partner_id = get_user_partner(user_id)
    
    if not partner_id:
        update.message.reply_text("❌ You need to be in a chat to report someone.")
        return
    
    if len(context.args) == 0:
        update.message.reply_text("❌ Please provide a reason for the report.\nUsage: /report <reason>")
        return
    
    reason = ' '.join(context.args)
    complaint_id = add_complaint(user_id, partner_id, reason)
    
    # Notify admin
    admin_text = f"""
🚨 **New Report**
ID: {complaint_id}
Reporter: {user_id}
Reported: {partner_id}
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    try:
        context.bot.send_message(ADMIN_ID, admin_text, parse_mode=ParseMode.MARKDOWN)
    except:
        pass
    
    update.message.reply_text("✅ Report submitted successfully. Thank you for keeping our community safe!")

# Admin Commands
def ban_command(update: Update, context: CallbackContext):
    """Admin command to ban user"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin only command!")
        return
    
    if len(context.args) != 1:
        update.message.reply_text("❌ Usage: /ban <user_id>")
        return
    
    try:
        target_user_id = int(context.args[0])
        ban_user(target_user_id)
        update.message.reply_text(f"✅ User {target_user_id} has been banned.")
    except ValueError:
        update.message.reply_text("❌ Invalid user ID.")

def unban_command(update: Update, context: CallbackContext):
    """Admin command to unban user"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin only command!")
        return
    
    if len(context.args) != 1:
        update.message.reply_text("❌ Usage: /unban <user_id>")
        return
    
    try:
        target_user_id = int(context.args[0])
        unban_user(target_user_id)
        update.message.reply_text(f"✅ User {target_user_id} has been unbanned.")
    except ValueError:
        update.message.reply_text("❌ Invalid user ID.")

def stats_command(update: Update, context: CallbackContext):
    """Admin command to view stats"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin only command!")
        return
    
    stats = get_bot_stats()
    stats_text = f"""
📊 **Bot Statistics**

👥 Total Users: {stats['total_users']}
🔗 Active Chats: {stats['active_chats']}
⏳ Waiting Users: {stats['waiting_users']}
🚫 Banned Users: {stats['banned_users']}
🌟 VIP Users: {stats['vip_users']}
🚨 Total Reports: {stats['total_complaints']}
"""
    
    update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

def broadcast_command(update: Update, context: CallbackContext):
    """Admin command to broadcast message"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin only command!")
        return
    
    if len(context.args) == 0:
        update.message.reply_text("❌ Usage: /broadcast <message>")
        return
    
    message = ' '.join(context.args)
    users = get_all_users()
    sent_count = 0
    
    for user_id in users:
        try:
            context.bot.send_message(user_id, f"📢 **Admin Broadcast**\n\n{message}", parse_mode=ParseMode.MARKDOWN)
            sent_count += 1
        except:
            continue
    
    update.message.reply_text(f"✅ Broadcast sent to {sent_count} users.")

def give_diamonds_command(update: Update, context: CallbackContext):
    """Admin command to give diamonds"""
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Admin only command!")
        return
    
    if len(context.args) != 2:
        update.message.reply_text("❌ Usage: /give_diamonds <user_id> <amount>")
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        add_user_diamonds(target_user_id, amount)
        update.message.reply_text(f"✅ Gave {amount} 💎 diamonds to user {target_user_id}.")
    except ValueError:
        update.message.reply_text("❌ Invalid user ID or amount.")

def handle_message(update: Update, context: CallbackContext):
    """Handle regular messages"""
    user_id = update.effective_user.id
    
    if is_user_banned(user_id):
        return
    
    partner_id = get_user_partner(user_id)
    
    if not partner_id:
        update.message.reply_text("❌ You're not connected to anyone. Use /next to find someone to chat with!")
        return
    
    # Get message text
    message_text = update.message.text
    
    if not message_text:
        update.message.reply_text("❌ Only text messages are supported in this version.")
        return
    
    # Check if translation is needed
    user_lang = get_user_language(user_id)
    partner_lang = get_user_language(partner_id)
    
    # Check if user has translation enabled and is VIP
    user_data = get_user_data(user_id)
    translation_enabled = user_data.get('translation_enabled', False)
    
    if translation_enabled and is_user_vip(user_id) and user_lang != partner_lang:
        translated_text = translate_message(message_text, user_lang, partner_lang)
        if translated_text:
            message_text = f"{translated_text}\n\n🌐 _Translated from {user_lang} to {partner_lang}_"
    
    try:
        context.bot.send_message(partner_id, message_text, parse_mode=ParseMode.MARKDOWN)
    except:
        context.bot.send_message(partner_id, message_text)

def handle_callback(update: Update, context: CallbackContext):
    """Handle callback queries from inline keyboards"""
    query = update.callback_query
    query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "referral_top":
        top_referrals = get_top_referrals()
        if top_referrals:
            text = "🏆 **Top Referrals**\n\n"
            for i, (uid, count) in enumerate(top_referrals[:10], 1):
                user_data = get_user_data(uid)
                username = user_data.get('username', 'Anonymous')
                text += f"{i}. {username}: {count} referrals\n"
        else:
            text = "🏆 **Top Referrals**\n\nNo referrals yet!"
        
        query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    elif data == "profile":
        profile_command(update, context)
    
    elif data == "rules":
        rules_command(update, context)
    
    elif data == "photo_roulette":
        query.edit_message_text("📸 **Photo Roulette**\n\nThis feature is coming soon! Stay tuned for updates.")
    
    elif data == "premium":
        premium_text = """
💎 **Premium Features**

🌟 VIP Benefits:
• 🚹🚺 Gender matching
• 🎂 Age range matching  
• 🌐 Auto translation
• 👀 Profile preview
• ⚡ Priority matching
• 💬 Unlimited chats

💰 **VIP Packages:**
1 Day - 500 💎
2 Days - 1000 💎  
3 Days - 1500 💎
5 Days - 2000 💎

Use /menu → Get VIP Status to purchase!
"""
        query.edit_message_text(premium_text, parse_mode=ParseMode.MARKDOWN)
    
    elif data == "get_vip":
        diamonds = get_user_diamonds(user_id)
        keyboard = [
            [InlineKeyboardButton("1 Day (500💎)", callback_data="buy_vip_1")],
            [InlineKeyboardButton("2 Days (1000💎)", callback_data="buy_vip_2")],
            [InlineKeyboardButton("3 Days (1500💎)", callback_data="buy_vip_3")],
            [InlineKeyboardButton("5 Days (2000💎)", callback_data="buy_vip_5")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"🌟 **Get VIP Status**\n\nYour diamonds: {diamonds} 💎\n\nChoose a VIP package:"
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    elif data.startswith("buy_vip_"):
        days = int(data.split("_")[-1])
        cost = days * 500 if days <= 2 else (1500 if days == 3 else 2000)
        
        diamonds = get_user_diamonds(user_id)
        if diamonds >= cost:
            add_user_diamonds(user_id, -cost)
            add_user_vip_days(user_id, days)
            query.edit_message_text(f"✅ VIP activated for {days} days! Enjoy your premium features!")
        else:
            query.edit_message_text(f"❌ Not enough diamonds! You need {cost} 💎 but have {diamonds} 💎")
    
    elif data == "translate_status":
        user_data = get_user_data(user_id)
        translation_enabled = user_data.get('translation_enabled', False)
        
        if not is_user_vip(user_id):
            query.edit_message_text("❌ Translation feature is only available for VIP users!")
            return
        
        keyboard = [
            [InlineKeyboardButton("✅ ON" if translation_enabled else "ON", callback_data="toggle_translation_on")],
            [InlineKeyboardButton("❌ OFF" if not translation_enabled else "OFF", callback_data="toggle_translation_off")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status = "ON" if translation_enabled else "OFF"
        text = f"🌐 **Translation Status**\n\nCurrent status: {status}\n\nAuto-translate messages between different languages."
        query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    elif data == "toggle_translation_on":
        set_user_translation(user_id, True)
        query.edit_message_text("✅ Translation turned ON! Messages will be auto-translated.")
    
    elif data == "toggle_translation_off":
        set_user_translation(user_id, False)
        query.edit_message_text("❌ Translation turned OFF.")
    
    elif data == "settings":
        keyboard = [
            [InlineKeyboardButton("👥 Set Gender", callback_data="set_gender"),
             InlineKeyboardButton("🎂 Set Age", callback_data="set_age")],
            [InlineKeyboardButton("🌐 Set Language", callback_data="set_language")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text("⚙️ **Settings**\n\nChoose what to configure:", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    
    elif data == "back_menu":
        menu_command(update, context)
