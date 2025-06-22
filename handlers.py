import logging
from datetime import datetime, timedelta

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Database & Logic imports
from database import (
    get_user, create_user, update_user, is_user_vip, add_diamonds, spend_diamonds,
    give_vip, find_available_partner, connect_users, disconnect_users,
    add_complaint, log_chat_message, get_user_stats, get_top_referrals,
    ban_user as db_ban_user, unban_user as db_unban_user,
    load_json, save_json, load_users, save_users
)

from translation import get_translation_info, get_available_languages

from photo_roulette import (
    upload_photo, get_random_photo, vote_photo, get_photo_stats, get_user_photos
)

from config import ADMIN_ID, VIP_PACKAGES, DAILY_BONUS, COMPLAINTS_DB, CHAT_LOGS_DB

logger = logging.getLogger(__name__)

# Helper function to check if user is admin
def is_admin(user_id):
    return user_id == ADMIN_ID

# Helper function to get main menu keyboard
def get_main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔝 Referral TOP", callback_data="referral_top"),
            InlineKeyboardButton("👤 Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton("📋 Rules", callback_data="rules"),
            InlineKeyboardButton("📸 Photo Roulette", callback_data="photo_roulette")
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
            InlineKeyboardButton("⭐ Get VIP Status", callback_data="get_vip")
        ],
        [
            InlineKeyboardButton("🌐 Translate Status", callback_data="translate_status"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    user = get_user(user_id)
    if not user:
        # Handle referral if present
        referred_by = None
        if context.args and context.args[0].startswith('ref_'):
            try:
                referred_by = int(context.args[0][4:])
                referrer = get_user(referred_by)
                if referrer and referred_by != user_id:
                    # Add referral
                    referrer['referrals'] = referrer.get('referrals', [])
                    referrer['referrals'].append(user_id)
                    add_diamonds(referred_by, 100)  # Referral bonus
            except ValueError:
                pass
        
        user = create_user(user_id, username, first_name)
        if referred_by:
            update_user(user_id, referred_by=referred_by)
            add_diamonds(user_id, 50)  # Welcome bonus for referred user
    
    if user.get('banned'):
        await update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    welcome_text = f"""
🎉 <b>Welcome to Anonymous Chat Bot!</b> 🎉

Hello {first_name}! 👋

🌐 Connect with strangers anonymously
💬 Chat without revealing your identity
⭐ Upgrade to VIP for premium features
💎 Current Diamonds: {user.get('diamonds', 0)}

Use /menu to access all features or /next to start chatting!

<i>By using this bot, you agree to follow our community rules. Type /rules to read them.</i>
"""
    
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.HTML)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    partner_id = user.get('current_partner')
    if partner_id:
        disconnect_users(user_id, partner_id)
        await update.message.reply_text("🚫 <b>Chat stopped!</b>\n\nUse /next to find a new partner.", parse_mode=ParseMode.HTML)
        
        # Notify partner
        try:
            await context.bot.send_message(
                chat_id=partner_id,
                text="🚫 <b>Your partner left the chat.</b>\n\nUse /next to find a new partner.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying partner: {e}")
    else:
        update_user(user_id, waiting_for_partner=False)
        await update.message.reply_text("❌ You're not in a chat right now.")

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /next command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    # Disconnect from current partner if any
    current_partner = user.get('current_partner')
    if current_partner:
        disconnect_users(user_id, current_partner)
        try:
            await context.bot.send_message(
                chat_id=current_partner,
                text="🔃 <b>Your partner found a new chat.</b>\n\nUse /next to find a new partner.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error notifying previous partner: {e}")
    
    # Set user as waiting for partner
    update_user(user_id, waiting_for_partner=True)
    
    # Try to find a partner
    partner_id = find_available_partner(user_id)
    
    if partner_id:
        connect_users(user_id, int(partner_id))
        
        # Get partner info
        partner = get_user(int(partner_id))
        user_vip_status = "⭐ VIP" if is_user_vip(user_id) else "👤 User"
        partner_vip_status = "⭐ VIP" if is_user_vip(int(partner_id)) else "👤 User"
        
        user_msg = f"✅ <b>Connected!</b> 🎉\n\nYou're now chatting with a stranger.\nYour status: {user_vip_status}\nPartner status: {partner_vip_status}\n\nUse /stop to end chat or /report to report inappropriate behavior."
        partner_msg = f"✅ <b>Connected!</b> 🎉\n\nYou're now chatting with a stranger.\nYour status: {partner_vip_status}\nPartner status: {user_vip_status}\n\nUse /stop to end chat or /report to report inappropriate behavior."
        
        await update.message.reply_text(user_msg, parse_mode=ParseMode.HTML)
        await context.bot.send_message(chat_id=int(partner_id), text=partner_msg, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("⏳ <b>Searching for a partner...</b>\n\nWe'll connect you as soon as someone becomes available!", parse_mode=ParseMode.HTML)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    vip_status = "⭐ VIP User" if is_user_vip(user_id) else "👤 Regular User"
    diamonds = user.get('diamonds', 0)
    
    menu_text = f"""
🔑 <b>Main Menu</b>

👋 Welcome, {user.get('first_name', 'User    ')}!
💎 Diamonds: {diamonds}
🏆 Status: {vip_status}

Choose an option below:
"""
    
    await update.message.reply_text(
        menu_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bonus command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    last_bonus = user.get('last_bonus')
    now = datetime.now()
    
    if last_bonus:
        last_bonus_date = datetime.fromisoformat(last_bonus)
        if now.date() == last_bonus_date.date():
            next_bonus = (last_bonus_date + timedelta(days=1)).strftime("%H:%M")
            await update.message.reply_text(f"⏰ You already claimed your daily bonus today!\n\nNext bonus available tomorrow at {next_bonus}")
            return
    
    add_diamonds(user_id, DAILY_BONUS)
    update_user(user_id, last_bonus=now.isoformat())
    
    await update.message.reply_text(f"🎁 <b>Daily Bonus Claimed!</b>\n\n+{DAILY_BONUS} 💎 Diamonds\n\nCome back tomorrow for another bonus!", parse_mode=ParseMode.HTML)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    vip_status = "⭐ VIP User" if is_user_vip(user_id) else "👤 Regular User"
    vip_until = ""
    
    if is_user_vip(user_id) and user_id != ADMIN_ID:
        vip_date = datetime.fromisoformat(user['vip_until'])
        vip_until = f"\n⏰ VIP Until: {vip_date.strftime('%Y-%m-%d %H:%M')}"
    elif user_id == ADMIN_ID:
        vip_until = "\n👑 Lifetime VIP (Admin)"
    
    profile_text = f"""
👤 <b>Your Profile</b>

🆔 User ID: {user_id}
👤 Name: {user.get('first_name', 'Unknown')}
📱 Username: @{user.get('username', 'None')}
👫 Gender: {user.get('gender', 'Not set')}
🎂 Age: {user.get('age', 'Not set')}
🌐 Language: {user.get('language', 'en')}
💎 Diamonds: {user.get('diamonds', 0)}
🏆 Status: {vip_status}{vip_until}
📈 Referrals: {len(user.get('referrals', []))}
📸 Photo Likes: {user.get('photo_likes', 0)}
"""
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Edit Profile", callback_data="edit_profile")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    
    await update.message.reply_text(
        profile_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rules command."""
    try:
        with open('rules.txt', 'r', encoding='utf-8') as f:
            rules_text = f.read()
    except FileNotFoundError:
        rules_text = """
📋 <b>Community Rules</b>

1. 🚫 No harassment, bullying, or inappropriate behavior
2. 🔞 No sharing of adult content or explicit material
3. 💬 Be respectful and kind to other users
4. 🚫 No spam, advertising, or promotional content
5. 🔒 Respect privacy - don't ask for personal information
6. 🚫 No hate speech, discrimination, or offensive language
7. 👮‍♂️ Report inappropriate behavior using /report
8. 🎯 Use the bot for its intended purpose only
9. 🚫 No ban evasion or creating multiple accounts
10. ⚖️ Admin decisions are final

<b>Violations may result in temporary or permanent bans.</b>

Thank you for helping us maintain a safe and friendly community! 🤝
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    
    await update.message.reply_text(
        rules_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all non-command messages."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    partner_id = user.get('current_partner')
    if not partner_id:
        await update.message.reply_text("❌ You're not in a chat. Use /next to find a partner!")
        return
    
    # Check if partner still exists and is connected
    partner = get_user(partner_id)
    if not partner or partner.get('current_partner') != user_id:
        update_user(user_id, current_partner=None)
        await update.message.reply_text("❌ Your partner has disconnected. Use /next to find a new one!")
        return
    
    try:
        message_type = "text"
        content = ""
        
        if update.message.text:
            message_type = "text"
            content = update.message.text
            
            # Handle translation if enabled
            translated_content, was_translated = get_translation_info(user_id, partner_id, content)
            
            await context.bot.send_message(
                chat_id=partner_id,
                text=translated_content,
                parse_mode=ParseMode.HTML if was_translated else None
            )
        
        elif update.message.sticker:
            message_type = "sticker"
            content = update.message.sticker.file_id
            await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
        
        elif update.message.photo:
            message_type = "photo"
            content = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            
            # Handle photo caption translation
            if caption:
                translated_caption, was_translated = get_translation_info(user_id, partner_id, caption)
                await context.bot.send_photo(
                    chat_id=partner_id,
                    photo=update.message.photo[-1].file_id,
                    caption=translated_caption,
                    parse_mode=ParseMode.HTML if was_translated else None
                )
            else:
                await context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1].file_id)
        
        elif update.message.voice:
            message_type = "voice"
            content = update.message.voice.file_id
            await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id)
        
        elif update.message.video:
            message_type = "video"
            content = update.message.video.file_id
            await context.bot.send_video(chat_id=partner_id, video=update.message.video.file_id)
        
        elif update.message.document:
            message_type = "document"
            content = update.message.document.file_id
            await context.bot.send_document(chat_id=partner_id, document=update.message.document.file_id)
        
        # Log the message for admin monitoring
        log_chat_message(user_id, partner_id, message_type, content)
        
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        await update.message.reply_text("❌ Failed to send message. Your partner may have disconnected.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    data = query.data
    
    if data == "referral_top":
        await show_referral_top(query, context)
    elif data == "profile":
        await show_profile_menu(query, context)
    elif data == "rules":
        await show_rules(query, context)
    elif data == "photo_roulette":
        await show_photo_roulette(query, context)
    elif data == "premium":
        await show_premium_features(query, context)
    elif data == "get_vip":
        await show_vip_packages(query, context)
    elif data == "translate_status":
        await show_translate_status(query, context)
    elif data == "settings":
        await show_settings(query, context)
    elif data == "back_to_menu":
        await show_main_menu(query, context)
    elif data.startswith("buy_vip_"):
        await handle_vip_purchase(query, context, data)
    elif data.startswith("toggle_translation"):
        await toggle_translation(query, context)
    elif data.startswith("set_language_"):
        await set_language(query, context, data)
    elif data.startswith("set_gender_"):
        await set_gender(query, context, data)
    elif data.startswith("photo_"):
        await handle_photo_action(query, context, data)

async def show_referral_top(query, context):
    """Show top referrals."""
    top_referrals = get_top_referrals()
    
    text = "🔝 <b>Top Referrals</b>\n\n"
    
    if not top_referrals:
        text += "📭 No referrals yet!\n\nInvite friends using your referral link to appear here."
    else:
        for i, ref in enumerate(top_referrals, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            username = f"@{ref['username']}" if ref['username'] else "Hidden"
            text += f"{medal} {ref['first_name']} ({username}) - {ref['referral_count']} referrals\n"
    
    user_id = query.from_user.id
    referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    text += f"\n🔗 <b>Your referral link:</b>\n<code>{referral_link}</code>"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
async def show_profile_menu(query, context):
    """Show profile menu."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    vip_status = "⭐ VIP User" if is_user_vip(user_id) else "👤 Regular User"
    
    text = f"""
👤 <b>Your Profile</b>

👤 Name: {user.get('first_name', 'Unknown')}
👫 Gender: {user.get('gender', 'Not set')}
🎂 Age: {user.get('age', 'Not set')}
🌐 Language: {user.get('language', 'en')}
💎 Diamonds: {user.get('diamonds', 0)}
🏆 Status: {vip_status}
📈 Referrals: {len(user.get('referrals', []))}
"""
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Edit Profile", callback_data="edit_profile")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_rules(query, context):
    """Show the rules."""
    try:
        with open('rules.txt', 'r', encoding='utf-8') as f:
            rules_text = f.read()
    except FileNotFoundError:
        rules_text = """
📋 <b>Community Rules</b>

1. 🚫 No harassment, bullying, or inappropriate behavior
2. 🔞 No sharing of adult content or explicit material
3. 💬 Be respectful and kind to other users
4. 🚫 No spam, advertising, or promotional content
5. 🔒 Respect privacy - don't ask for personal information
6. 🚫 No hate speech, discrimination, or offensive language
7. 👮‍♂️ Report inappropriate behavior using /report
8. 🎯 Use the bot for its intended purpose only
9. 🚫 No ban evasion or creating multiple accounts
10. ⚖️ Admin decisions are final

<b>Violations may result in temporary or permanent bans.</b>

Thank you for helping us maintain a safe and friendly community! 🤝
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    
    await query.edit_message_text(
        rules_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all non-command messages."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    partner_id = user.get('current_partner')
    if not partner_id:
        await update.message.reply_text("❌ You're not in a chat. Use /next to find a partner!")
        return
    
    # Check if partner still exists and is connected
    partner = get_user(partner_id)
    if not partner or partner.get('current_partner') != user_id:
        update_user(user_id, current_partner=None)
        await update.message.reply_text("❌ Your partner has disconnected. Use /next to find a new one!")
        return
    
    try:
        message_type = "text"
        content = ""
        
        if update.message.text:
            message_type = "text"
            content = update.message.text
            
            # Handle translation if enabled
            translated_content, was_translated = get_translation_info(user_id, partner_id, content)
            
            await context.bot.send_message(
                chat_id=partner_id,
                text=translated_content,
                parse_mode=ParseMode.HTML if was_translated else None
            )
        
        elif update.message.sticker:
            message_type = "sticker"
            content = update.message.sticker.file_id
            await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
        
        elif update.message.photo:
            message_type = "photo"
            content = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            
            # Handle photo caption translation
            if caption:
                translated_caption, was_translated = get_translation_info(user_id, partner_id, caption)
                await context.bot.send_photo(
                    chat_id=partner_id,
                    photo=update.message.photo[-1].file_id,
                    caption=translated_caption,
                    parse_mode=ParseMode.HTML if was_translated else None
                )
            else:
                await context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1].file_id)
        
        elif update.message.voice:
            message_type = "voice"
            content = update.message.voice.file_id
            await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id)
        
        elif update.message.video:
            message_type = "video"
            content = update.message.video.file_id
            await context.bot.send_video(chat_id=partner_id, video=update.message.video.file_id)
        
        elif update.message.document:
            message_type = "document"
            content = update.message.document.file_id
            await context.bot.send_document(chat_id=partner_id, document=update.message.document.file_id)
        
        # Log the message for admin monitoring
        log_chat_message(user_id, partner_id, message_type, content)
        
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        await update.message.reply_text("❌ Failed to send message. Your partner may have disconnected.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    data = query.data
    
    if data == "referral_top":
        await show_referral_top(query, context)
    elif data == "profile":
        await show_profile_menu(query, context)
    elif data == "rules":
        await show_rules(query, context)
    elif data == "photo_roulette":
        await show_photo_roulette(query, context)
    elif data == "premium":
        await show_premium_features(query, context)
    elif data == "get_vip":
        await show_vip_packages(query, context)
    elif data == "translate_status":
        await show_translate_status(query, context)
    elif data == "settings":
        await show_settings(query, context)
    elif data == "back_to_menu":
        await show_main_menu(query, context)
    elif data.startswith("buy_vip_"):
        await handle_vip_purchase(query, context, data)
    elif data.startswith("toggle_translation"):
        await toggle_translation(query, context)
    elif data.startswith("set_language_"):
        await set_language(query, context, data)
    elif data.startswith("set_gender_"):
        await set_gender(query, context, data)
    elif data.startswith("photo_"):
        await handle_photo_action(query, context, data)

async def show_referral_top(query, context):
    """Show top referrals."""
    top_referrals = get_top_referrals()
    
    text = "🔝 <b>Top Referrals</b>\n\n"
    
    if not top_referrals:
        text += "📭 No referrals yet!\n\nInvite friends using your referral link to appear here."
    else:
        for i, ref in enumerate(top_referrals, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            username = f"@{ref['username']}" if ref['username'] else "Hidden"
            text += f"{medal} {ref['first_name']} ({username}) - {ref['referral_count']} referrals\n"
    
    user_id = query.from_user.id
    referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    text += f"\n🔗 <b>Your referral link:</b>\n<code>{referral_link}</code>"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_profile_menu(query, context):
    """Show profile menu."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    vip_status = "⭐ VIP User" if is_user_vip(user_id) else "👤 Regular User"
    
    text = f"""
👤 <b>Your Profile</b>

👤 Name: {user.get('first_name', 'Unknown')}
👫 Gender: {user.get('gender', 'Not set')}
🎂 Age: {user.get('age', 'Not set')}
🌐 Language: {user.get('language', 'en')}
💎 Diamonds: {user.get('diamonds', 0)}
🏆 Status: {vip_status}
📈 Referrals: {len(user.get('referrals', []))}
"""
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Edit Profile", callback_data="edit_profile")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_rules(query, context):
    """Show the rules."""
    try:
        with open('rules.txt', 'r', encoding='utf-8') as f:
            rules_text = f.read()
    except FileNotFoundError:
        rules_text = """
📋 <b>Community Rules</b>

1. 🚫 No harassment, bullying, or inappropriate behavior
2. 🔞 No sharing of adult content or explicit material
3. 💬 Be respectful and kind to other users
4. 🚫 No spam, advertising, or promotional content
5. 🔒 Respect privacy - don't ask for personal information
6. 🚫 No hate speech, discrimination, or offensive language
7. 👮‍♂️ Report inappropriate behavior using /report
8. 🎯 Use the bot for its intended purpose only
9. 🚫 No ban evasion or creating multiple accounts
10. ⚖️ Admin decisions are final

<b>Violations may result in temporary or permanent bans.</b>

Thank you for helping us maintain a safe and friendly community! 🤝
"""
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    
    await query.edit_message_text(
        rules_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all non-command messages."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    partner_id = user.get('current_partner')
    if not partner_id:
        await update.message.reply_text("❌ You're not in a chat. Use /next to find a partner!")
        return
    
    # Check if partner still exists and is connected
    partner = get_user(partner_id)
    if not partner or partner.get('current_partner') != user_id:
        update_user(user_id, current_partner=None)
        await update.message.reply_text("❌ Your partner has disconnected. Use /next to find a new one!")
        return
    
    try:
        message_type = "text"
        content = ""
        
        if update.message.text:
            message_type = "text"
            content = update.message.text
            
            # Handle translation if enabled
            translated_content, was_translated = get_translation_info(user_id, partner_id, content)
            
            await context.bot.send_message(
                chat_id=partner_id,
                text=translated_content,
                parse_mode=ParseMode.HTML if was_translated else None
            )
        
        elif update.message.sticker:
            message_type = "sticker"
            content = update.message.sticker.file_id
            await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
        
        elif update.message.photo:
            message_type = "photo"
            content = update.message.photo[-1].file_id
            caption = update.message.caption or ""
            
            # Handle photo caption translation
            if caption:
                translated_caption, was_translated = get_translation_info(user_id, partner_id, caption)
                await context.bot.send_photo(
                    chat_id=partner_id,
                    photo=update.message.photo[-1].file_id,
                    caption=translated_caption,
                    parse_mode=ParseMode.HTML if was_translated else None
                )
            else:
                await context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1].file_id)
        
        elif update.message.voice:
            message_type = "voice"
            content = update.message.voice.file_id
            await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id)
        
        elif update.message.video:
            message_type = "video"
            content = update.message.video.file_id
            await context.bot.send_video(chat_id=partner_id, video=update.message.video.file_id)
        
        elif update.message.document:
            message_type = "document"
            content = update.message.document.file_id
            await context.bot.send_document(chat_id=partner_id, document=update.message.document.file_id)
        
        # Log the message for admin monitoring
        log_chat_message(user_id, partner_id, message_type, content)
        
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        await update.message.reply_text("❌ Failed to send message. Your partner may have disconnected.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    data = query.data
    
    if data == "referral_top":
        await show_referral_top(query, context)
    elif data == "profile":
        await show_profile_menu(query, context)
    elif data == "rules":
        await show_rules(query, context)
    elif data == "photo_roulette":
        await show_photo_roulette(query, context)
    elif data == "premium":
        await show_premium_features(query, context)
    elif data == "get_vip":
        await show_vip_packages(query, context)
    elif data == "translate_status":
        await show_translate_status(query, context)
    elif data == "settings":
        await show_settings(query, context)
    elif data == "back_to_menu":
        await show_main_menu(query, context)
    elif data.startswith("buy_vip_"):
        await handle_vip_purchase(query, context, data)
    elif data.startswith("toggle_translation"):
        await toggle_translation(query, context)
    elif data.startswith("set_language_"):
        await set_language(query, context, data)
    elif data.startswith("set_gender_"):
        await set_gender(query, context, data)
    elif data.startswith("photo_"):
        await handle_photo_action(query, context, data)

async def show_referral_top(query, context):
    """Show top referrals."""
    top_referrals = get_top_referrals()
    
    text = "🔝 <b>Top Referrals</b>\n\n"
    
    if not top_referrals:
        text += "📭 No referrals yet!\n\nInvite friends using your referral link to appear here."
    else:
        for i, ref in enumerate(top_referrals, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            username = f"@{ref['username']}" if ref['username'] else "Hidden"
            text += f"{medal} {ref['first_name']} ({username}) - {ref['referral_count']} referrals\n"
    
    user_id = query.from_user.id
    referral_link = f"https://t.me/{context.bot.username}?start=ref_{user_id}"
    text += f"\n🔗 <b>Your referral link:</b>\n<code>{referral_link}</code>"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    
async def show_photo_roulette(query, context):
    """Show photo roulette options."""
    text = "📸 <b>Photo Roulette</b>\n\n" \
           "In this game, you can share photos and vote on them!\n\n" \
           "Choose an option below:"
    
    keyboard = [
        [InlineKeyboardButton("🎲 Upload Photo", callback_data="upload_photo")],
        [InlineKeyboardButton("🖼️ View Random Photo", callback_data="view_random_photo")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def upload_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo upload."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    await update.message.reply_text("📤 Please send the photo you want to upload.")

async def handle_uploaded_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the uploaded photo."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        # Save the photo to the database or process it as needed
        await update.message.reply_text("✅ Your photo has been uploaded successfully!")
        # Optionally, you can add logic to store the photo ID in the database
    else:
        await update.message.reply_text("❌ Please send a valid photo.")

async def view_random_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show a random photo from the roulette."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    random_photo = get_random_photo()
    
    if random_photo:
        await update.message.reply_photo(photo=random_photo['file_id'], caption=random_photo.get('caption', ""))
    else:
        await update.message.reply_text("❌ No photos available at the moment.")

async def vote_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voting on a photo."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    # Logic to handle voting on a specific photo
    # This could involve checking the photo ID and updating the vote count in the database
    await update.message.reply_text("🗳️ Please vote for the photo by sending its ID.")

async def get_photo_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics for a specific photo."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    # Logic to retrieve and display photo statistics
    await update.message.reply_text("📊 Here are the statistics for the photo...")

async def show_vip_packages(query, context):
    """Show available VIP packages."""
    text = "💎 <b>VIP Packages</b>\n\n" \
           "Choose a package to upgrade your status:\n"
    
    for package in VIP_PACKAGES:
        text += f"{package['name']} - {package['price']} Diamonds\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def handle_vip_purchase(query, context, data):
    """Handle VIP package purchase."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    package_id = data.split("_")[2]  # Extract package ID from callback data
    package = next((pkg for pkg in VIP_PACKAGES if pkg['id'] == package_id), None)
    
    if package:
        if user.get('diamonds', 0) >= package['price']:
            spend_diamonds(user_id, package['price'])
            give_vip(user_id, package['duration'])
            await query.edit_message_text(f"✅ You have successfully purchased the {package['name']} package!")
        else:
            await query.edit_message_text("❌ You do not have enough diamonds to purchase this package.")
    else:
        await query.edit_message_text("❌ Invalid package selection.")

async def toggle_translation(query, context):
    """Toggle translation feature."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    user['translation_enabled'] = not user.get('translation_enabled', False)
    update_user(user_id, translation_enabled=user['translation_enabled'])
    
    status = "enabled" if user['translation_enabled'] else "disabled"
    await query.edit_message_text(f"🔄 Translation feature has been {status}.")

async def set_language(query, context, data):
    """Set user language preference."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    language_code = data.split("_")[2]  # Extract language code from callback data
    user['language'] = language_code
    update_user(user_id, language=language_code)
    
    await query.edit_message_text(f"🌐 Language has been set to {get_available_languages()[language_code]}.")

async def set_gender(query, context, data):
    """Set user gender preference."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    gender = data.split("_")[2]  # Extract gender from callback data
    user['gender'] = gender
    update_user(user_id, gender=gender)
    
    await query.edit_message_text(f"👫 Gender has been set to {gender}.")

async def handle_photo_action(query, context, data):
    """Handle actions related to photos."""
    action = data.split("_")[1]  # Extract action from callback data
    
    if action == "upload":
        await upload_photo(query, context)
    elif action == "vote":
        await vote_photo(query, context)
    elif action == "stats":
        await get_photo_stats(query, context)

async def show_settings(query, context):
    """Show user settings."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    text = "⚙️ <b>Settings</b>\n\n" \
           f"🌐 Language: {user.get('language', 'en')}\n" \
           f"👫 Gender: {user.get('gender', 'Not set')}\n" \
           f"🔄 Translation: {'Enabled' if user.get('translation_enabled', False) else 'Disabled'}\n"
    
    keyboard = [
        [InlineKeyboardButton("🌐 Change Language", callback_data="change_language")],
        [InlineKeyboardButton("👫 Change Gender", callback_data="change_gender")],
        [InlineKeyboardButton("🔄 Toggle Translation", callback_data="toggle_translation")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_main_menu(query, context):
    """Show the main menu."""
    await query.edit_message_text(
        "🔑 <b>Main Menu</b>\n\nChoose an option below:",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reporting a user."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    await update.message.reply_text("📝 Please provide the user ID or username of the user you want to report.")

async def add_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a complaint to the database."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    complaint_text = update.message.text
    add_complaint(user_id, complaint_text)
    
    await update.message.reply_text("✅ Your complaint has been submitted.")

async def log_chat_message(user_id, partner_id, message_type, content):
    """Log chat messages for monitoring."""
    log_entry = {
        'user_id': user_id,
        'partner_id': partner_id,
        'message_type': message_type,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    # Save log_entry to the database or a log file

# Add any additional functions or handlers below as needed
