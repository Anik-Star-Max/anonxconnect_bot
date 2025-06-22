import logging
from datetime import datetime, timedelta

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode  # ✅ Fixed
from telegram.ext import ContextTypes

# Database & Logic imports
from database import (
    get_user, create_user, update_user, is_user_vip, add_diamonds, spend_diamonds,
    give_vip, find_available_partner, connect_users, disconnect_users,
    add_complaint, log_chat_message, get_user_stats, get_top_referrals,
    ban_user as db_ban_user, unban_user as db_unban_user,
    load_json, save_json, load_users, save_users  # ✅ Add these
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
        except Exception:
            pass
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
        except Exception:
            pass
    
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

👋 Welcome, {user.get('first_name', 'User')}!
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
    """Show rules."""
    await rules(query, context)

async def show_photo_roulette(query, context):
    """Show photo roulette menu."""
    from photo_roulette import get_user_photos, get_random_photo
    
    user_id = query.from_user.id
    user_photos = get_user_photos(user_id)
    
    text = """
📸 <b>Photo Roulette</b>

Upload your photos for others to rate!
Get diamonds when people like your photos.

Your photos: {}
Total likes: {}
"""
    
    keyboard = [
        [
            InlineKeyboardButton("📤 Upload Photo", callback_data="photo_upload"),
            InlineKeyboardButton("🎲 Rate Photos", callback_data="photo_rate")
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="photo_stats"),
            InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")
        ]
    ]
    
    await query.edit_message_text(
        text.format(len(user_photos), sum(p.get('likes', 0) for p in user_photos)),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_premium_features(query, context):
    """Show premium features."""
    text = """
💎 <b>Premium Features</b>

⭐ VIP Benefits:
• 🎯 Gender matching
• 🎂 Age range selection
• 🌐 Auto translation
• 👀 Profile preview
• 📸 Photo roulette priority
• 💬 VIP badge in chats

🎁 Daily bonuses and special rewards!
"""
    
    keyboard = [
        [InlineKeyboardButton("⭐ Get VIP", callback_data="get_vip")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_vip_packages(query, context):
    """Show VIP packages."""
    user_id = query.from_user.id
    user = get_user(user_id)
    diamonds = user.get('diamonds', 0)
    
    text = f"""
⭐ <b>VIP Packages</b>

💎 Your Diamonds: {diamonds}

Choose a VIP package:
"""
    
    keyboard = []
    for package_id, package_info in VIP_PACKAGES.items():
        days = package_info['days']
        price = package_info['price']
        day_text = "day" if days == 1 else "days"
        affordable = "✅" if diamonds >= price else "❌"
        
        keyboard.append([
            InlineKeyboardButton(
                f"{affordable} {days} {day_text} - {price} 💎",
                callback_data=f"buy_vip_{package_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_translate_status(query, context):
    """Show translation status."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    is_vip = is_user_vip(user_id)
    translation_enabled = user.get('translation_enabled', False)
    
    if not is_vip:
        text = """
🌐 <b>Translation Power</b>

❌ VIP Required
You need VIP status to use auto-translation feature.

Upgrade to VIP to translate messages automatically!
"""
        keyboard = [
            [InlineKeyboardButton("⭐ Get VIP", callback_data="get_vip")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
        ]
    else:
        status = "🟢 ON" if translation_enabled else "🔴 OFF"
        text = f"""
🌐 <b>Translation Power</b>

Status: {status}

When enabled, messages will be automatically translated between you and your chat partner if you speak different languages.
"""
        
        keyboard = [
            [
                InlineKeyboardButton("🟢 Turn ON", callback_data="toggle_translation_on"),
                InlineKeyboardButton("🔴 Turn OFF", callback_data="toggle_translation_off")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
        ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_settings(query, context):
    """Show settings menu."""
    user_id = query.from_user.id
    user = get_user(user_id)
    is_vip = is_user_vip(user_id)
    
    text = f"""
⚙️ <b>Settings</b>

Current Settings:
👫 Gender: {user.get('gender', 'Not set')}
🎂 Age: {user.get('age', 'Not set')}
🌐 Language: {user.get('language', 'en')}

{('⭐ VIP Preferences:' if is_vip else '🔒 VIP Only:')}
🎯 Preferred Gender: {user.get('preferred_gender', 'any') if is_vip else 'Locked'}
📊 Age Range: {user.get('preferred_age_min', 18)}-{user.get('preferred_age_max', 99) if is_vip else 'Locked'}
"""
    
    keyboard = [
        [
            InlineKeyboardButton("👫 Set Gender", callback_data="set_gender"),
            InlineKeyboardButton("🎂 Set Age", callback_data="set_age")
        ],
        [InlineKeyboardButton("🌐 Set Language", callback_data="set_language")]
    ]
    
    if is_vip:
        keyboard.append([
            InlineKeyboardButton("🎯 VIP Preferences", callback_data="vip_preferences")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def show_main_menu(query, context):
    """Show main menu."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    vip_status = "⭐ VIP User" if is_user_vip(user_id) else "👤 Regular User"
    diamonds = user.get('diamonds', 0)
    
    menu_text = f"""
🔑 <b>Main Menu</b>

👋 Welcome, {user.get('first_name', 'User')}!
💎 Diamonds: {diamonds}
🏆 Status: {vip_status}

Choose an option below:
"""
    
    await query.edit_message_text(
        menu_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def handle_vip_purchase(query, context, data):
    """Handle VIP package purchase."""
    user_id = query.from_user.id
    user = get_user(user_id)
    
    package_id = data.replace("buy_vip_", "")
    if package_id not in VIP_PACKAGES:
        return
    
    package = VIP_PACKAGES[package_id]
    price = package['price']
    days = package['days']
    
    if user.get('diamonds', 0) < price:
        await query.answer("❌ Not enough diamonds!", show_alert=True)
        return
    
    if spend_diamonds(user_id, price):
        give_vip(user_id, days)
        
        day_text = "day" if days == 1 else "days"
        await query.answer(f"✅ VIP activated for {days} {day_text}!", show_alert=True)
        
        # Show updated menu
        await show_main_menu(query, context)
    else:
        await query.answer("❌ Purchase failed!", show_alert=True)

async def toggle_translation(query, context):
    """Toggle translation on/off."""
    user_id = query.from_user.id
    data = query.data
    
    if not is_user_vip(user_id):
        await query.answer("❌ VIP required!", show_alert=True)
        return
    
    enabled = data == "toggle_translation_on"
    update_user(user_id, translation_enabled=enabled)
    
    status = "enabled" if enabled else "disabled"
    await query.answer(f"🌐 Translation {status}!", show_alert=True)
    
    await show_translate_status(query, context)

# Admin commands
async def report_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user or user.get('banned'):
        return
    
    partner_id = user.get('current_partner')
    if not partner_id:
        await update.message.reply_text("❌ You're not in a chat to report anyone.")
        return
    
    reason = " ".join(context.args) if context.args else "No reason provided"
    complaint_id = add_complaint(user_id, partner_id, reason)
    
    # Notify admin
    try:
        admin_text = f"""
🚨 <b>New Report</b>

Report ID: {complaint_id}
Reporter: {user_id} ({user.get('first_name', 'Unknown')})
Reported User: {partner_id}
Reason: {reason}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        pass
    
    await update.message.reply_text("✅ Report submitted. Thank you for helping keep our community safe!")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /ban <user_id>")
        return
    
    try:
        target_user_id = int(context.args[0])
        if db_ban_user(target_user_id):
            # Disconnect user if in chat
            disconnect_users(target_user_id)
            await update.message.reply_text(f"✅ User {target_user_id} has been banned.")
        else:
            await update.message.reply_text("❌ User not found.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /unban <user_id>")
        return
    
    try:
        target_user_id = int(context.args[0])
        if db_unban_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been unbanned.")
        else:
            await update.message.reply_text("❌ User not found.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    stats = get_user_stats()
    
    stats_text = f"""
📊 <b>Bot Statistics</b>

👥 Total Users: {stats['total_users']}
💬 Active Chats: {stats['active_users']}
⭐ VIP Users: {stats['vip_users']}
🚫 Banned Users: {stats['banned_users']}
📝 Total Complaints: {stats['total_complaints']}
"""
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    message = " ".join(context.args)
    users = load_json('users.json')
    
    sent = 0
    failed = 0
    
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"📢 <b>Announcement</b>\n\n{message}",
                parse_mode=ParseMode.HTML
            )
            sent += 1
        except Exception:
            failed += 1
    
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users. {failed} failed.")

async def give_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /givevip command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /givevip <user_id> <days>")
        return
    
    try:
        target_user_id = int(context.args[0])
        days = int(context.args[1])
        
        if give_vip(target_user_id, days):
            await update.message.reply_text(f"✅ Gave {days} days of VIP to user {target_user_id}")
        else:
            await update.message.reply_text("❌ User not found.")
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments.")

async def give_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /givediamonds command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /givediamonds <user_id> <amount>")
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        
        new_balance = add_diamonds(target_user_id, amount)
        await update.message.reply_text(f"✅ Gave {amount} diamonds to user {target_user_id}. New balance: {new_balance}")
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments.")

async def view_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /complaints command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    complaints = load_json(COMPLAINTS_DB)
    
    if not complaints:
        await update.message.reply_text("📭 No complaints found.")
        return
    
    text = "📝 <b>Recent Complaints</b>\n\n"
    
    # Show last 10 complaints
    recent = list(complaints.values())[-10:]
    for complaint in recent:
        text += f"ID: {complaint['id']}\n"
        text += f"Reporter: {complaint['reporter_id']}\n"
        text += f"Reported: {complaint['reported_id']}\n"
        text += f"Reason: {complaint['reason']}\n"
        text += f"Time: {complaint['timestamp'][:19]}\n\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def view_user_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /viewchats command (Admin only)."""
    if not is_admin(update.effective_user.id):
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /viewchats <user_id>")
        return
    
    try:
        target_user_id = int(context.args[0])
        logs = load_json(CHAT_LOGS_DB)
        
        user_logs = [log for log in logs.values() 
                    if log['sender_id'] == target_user_id or log['receiver_id'] == target_user_id]
        
        if not user_logs:
            await update.message.reply_text(f"📭 No chat logs found for user {target_user_id}")
            return
        
        text = f"💬 <b>Chat Logs for User {target_user_id}</b>\n\n"
        
        # Show last 20 messages
        recent_logs = user_logs[-20:]
        for log in recent_logs:
            direction = "→" if log['sender_id'] == target_user_id else "←"
            text += f"{direction} {log['message_type']}: {log['content'][:50]}...\n"
            text += f"   {log['timestamp'][:19]}\n\n"
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
