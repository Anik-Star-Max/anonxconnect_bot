import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from database import *
from translation import get_translated_message
from config import *

logger = logging.getLogger(__name__)

# Start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    user = get_user(user_id)
    
    if not user:
        user = create_user(user_id, username, first_name)
        
        # Ask for gender
        keyboard = [
            [InlineKeyboardButton("👨 Male", callback_data="gender_male")],
            [InlineKeyboardButton("👩 Female", callback_data="gender_female")],
            [InlineKeyboardButton("🔄 Other", callback_data="gender_other")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"{WELCOME_MESSAGE}\n\n👤 Please select your gender:",
            reply_markup=reply_markup
        )
    else:
        if user.get('banned'):
            await update.message.reply_text("❌ You are banned from using this bot.")
            return
            
        await update.message.reply_text(
            f"🎉 Welcome back, {first_name}!\n\n"
            f"💎 Diamonds: {user.get('diamonds', 0)}\n"
            f"⭐ VIP Status: {'✅ Active' if is_vip(user_id) else '❌ Inactive'}\n\n"
            f"Use /menu to access all features!"
        )

# Menu command
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start first.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🏆 Referral TOP", callback_data="referral_top")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile")],
        [InlineKeyboardButton("📜 Rules", callback_data="rules")],
        [InlineKeyboardButton("📸 Photo Roulette", callback_data="photo_roulette")],
        [InlineKeyboardButton("💎 Premium", callback_data="premium")],
        [InlineKeyboardButton("⭐ Get VIP Status", callback_data="get_vip")],
        [InlineKeyboardButton("🌐 Translate Status", callback_data="translate_status")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    vip_status = "✅ Active" if is_vip(user_id) else "❌ Inactive"
    
    await update.message.reply_text(
        f"🎛️ **Main Menu**\n\n"
        f"👤 User: {user.get('first_name', 'Unknown')}\n"
        f"💎 Diamonds: {user.get('diamonds', 0)}\n"
        f"⭐ VIP: {vip_status}\n\n"
        f"Choose an option below:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

# Stop command
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start first.")
        return
    
    partner_id = disconnect_user(user_id)
    
    if partner_id:
        await update.message.reply_text("🛑 Chat stopped! Use /next to find a new partner.")
        try:
            await context.bot.send_message(
                partner_id, 
                "💔 Your partner has left the chat. Use /next to find someone new!"
            )
        except:
            pass
    else:
        await update.message.reply_text("❌ You're not in an active chat.")

# Next command
async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /next command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start first.")
        return
    
    if user.get('banned'):
        await update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    # Disconnect from current partner
    old_partner = disconnect_user(user_id)
    if old_partner:
        try:
            await context.bot.send_message(
                old_partner, 
                "💔 Your partner has left the chat. Use /next to find someone new!"
            )
        except:
            pass
    
    # Find new partner
    partner_id = find_partner(user_id)
    
    if partner_id:
        connect_users(user_id, partner_id)
        
        await update.message.reply_text(
            "🎉 Connected! You can now start chatting!\n"
            "🚫 Use /stop to end the chat\n"
            "🔄 Use /next to find a new partner\n"
            "🚨 Use /report to report inappropriate behavior"
        )
        
        try:
            await context.bot.send_message(
                partner_id,
                "🎉 Connected! You can now start chatting!\n"
                "🚫 Use /stop to end the chat\n"
                "🔄 Use /next to find a new partner\n"
                "🚨 Use /report to report inappropriate behavior"
            )
        except:
            disconnect_user(user_id)
            await update.message.reply_text("❌ Connection failed. Please try again.")
    else:
        # Add user to waiting list
        user['waiting'] = True
        save_user(user_id, user)
        
        await update.message.reply_text(
            "⏳ Searching for a partner... Please wait!\n"
            "🔍 You'll be connected automatically when someone joins."
        )

# Bonus command
async def bonus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /bonus command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start first.")
        return
    
    last_bonus = user.get('last_bonus')
    now = datetime.now()
    
    if last_bonus:
        last_bonus_date = datetime.fromisoformat(last_bonus)
        if (now - last_bonus_date).days < 1:
            next_bonus = last_bonus_date + timedelta(days=1)
            hours_left = int((next_bonus - now).total_seconds() / 3600)
            await update.message.reply_text(
                f"⏰ You already claimed your daily bonus!\n"
                f"Next bonus available in: {hours_left} hours"
            )
            return
    
    # Give daily bonus
    add_diamonds(user_id, DAILY_BONUS)
    user['last_bonus'] = now.isoformat()
    save_user(user_id, user)
    
    await update.message.reply_text(
        f"🎁 Daily bonus claimed!\n"
        f"💎 +{DAILY_BONUS} diamonds added to your account!\n"
        f"💰 Total diamonds: {user.get('diamonds', 0) + DAILY_BONUS}"
    )

# Profile command
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start first.")
        return
    
    vip_status = "✅ Active" if is_vip(user_id) else "❌ Inactive"
    vip_until = user.get('vip_until')
    
    if vip_until and is_vip(user_id):
        vip_date = datetime.fromisoformat(vip_until)
        vip_info = f"Until: {vip_date.strftime('%Y-%m-%d %H:%M')}"
    else:
        vip_info = "Not active"
    
    profile_text = f"""
👤 **Your Profile**

🆔 ID: {user_id}
👤 Name: {user.get('first_name', 'Not set')}
🚻 Gender: {user.get('gender', 'Not set')}
🎂 Age: {user.get('age', 'Not set')}
🌍 Language: {SUPPORTED_LANGUAGES.get(user.get('language', 'en'), 'English')}
💎 Diamonds: {user.get('diamonds', 0)}
⭐ VIP Status: {vip_status}
📅 VIP Info: {vip_info}
👥 Referrals: {user.get('referral_count', 0)}
📸 Photo Likes: {user.get('photo_likes', 0)}
📅 Joined: {user.get('registered', 'Unknown')[:10]}
"""
    
    keyboard = [
        [InlineKeyboardButton("✏️ Edit Profile", callback_data="edit_profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        profile_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

# Rules command
async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /rules command."""
    try:
        with open(RULES_FILE, 'r') as f:
            rules_text = f.read()
    except:
        rules_text = """
📜 **Community Rules**

1. 🚫 No harassment or bullying
2. 🔞 No explicit sexual content
3. 👶 No content involving minors
4. 🤝 Be respectful to other users
5. 🚭 No spam or advertising
6. 🔒 Protect your privacy
7. 🚨 Report inappropriate behavior
8. 💎 No diamond farming or cheating
9. 🎭 One account per person
10. ⚖️ Follow Telegram's Terms of Service

❗ Violation of these rules may result in permanent ban.
"""
    
    await update.message.reply_text(rules_text, parse_mode=ParseMode.MARKDOWN)

# Report command
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start first.")
        return
    
    partner_id = user.get('partner')
    if not partner_id:
        await update.message.reply_text("❌ You're not in an active chat.")
        return
    
    # Save complaint
    complaints = load_complaints()
    complaint_id = f"{user_id}_{partner_id}_{int(datetime.now().timestamp())}"
    
    complaints[complaint_id] = {
        'reporter': user_id,
        'reported': partner_id,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    save_complaints(complaints)
    
    # Notify admin
    try:
        await context.bot.send_message(
            ADMIN_ID,
            f"🚨 **New Report**\n\n"
            f"Reporter: {user_id}\n"
            f"Reported: {partner_id}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Complaint ID: {complaint_id}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    await update.message.reply_text(
        "✅ Report submitted successfully!\n"
        "🔍 Our team will review it shortly.\n"
        "⚖️ Appropriate action will be taken if needed."
    )

# Button callback handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    user = get_user(user_id)
    if not user:
        await query.edit_message_text("❌ Please use /start first.")
        return
    
    # Gender selection
    if data.startswith("gender_"):
        gender = data.split("_")[1]
        user['gender'] = gender
        save_user(user_id, user)
        
        # Ask for age
        keyboard = [
            [InlineKeyboardButton("📝 Set Age", callback_data="set_age")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ Gender set to: {gender.title()}\n\n"
            f"🎂 Now please set your age:",
            reply_markup=reply_markup
        )
    
    # Set age
    elif data == "set_age":
        await query.edit_message_text(
            "🎂 Please type your age (18-99):"
        )
        context.user_data['waiting_for_age'] = True
    
    # Referral TOP
    elif data == "referral_top":
        users = load_users()
        top_referrers = sorted(
            [(uid, u) for uid, u in users.items()], 
            key=lambda x: x[1].get('referral_count', 0),
            reverse=True
        )[:10]
        
        top_text = "🏆 **Referral TOP 10**\n\n"
        for i, (uid, u) in enumerate(top_referrers, 1):
            name = u.get('first_name', 'Anonymous')
            refs = u.get('referral_count', 0)
            if u.get('settings', {}).get('show_profile', True):
                top_text += f"{i}. {name} - {refs} referrals\n"
            else:
                top_text += f"{i}. Anonymous - {refs} referrals\n"
        
        await query.edit_message_text(top_text, parse_mode=ParseMode.MARKDOWN)
    
    # Profile
    elif data == "profile":
        await profile_command(update, context)
    
    # Rules
    elif data == "rules":
        await rules_command(update, context)
    
    # Photo Roulette
    elif data == "photo_roulette":
        keyboard = [
            [InlineKeyboardButton("📤 Upload Photo", callback_data="upload_photo")],
            [InlineKeyboardButton("👀 View Photos", callback_data="view_photos")],
            [InlineKeyboardButton("📊 My Stats", callback_data="photo_stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📸 **Photo Roulette**\n\n"
            "Upload your photos and rate others!\n"
            "Get likes and become popular!\n\n"
            "⭐ VIP users get priority display",
            reply_markup=reply_markup
        )
    
    # Premium
    elif data == "premium":
        await query.edit_message_text(VIP_FEATURES, parse_mode=ParseMode.MARKDOWN)
    
    # Get VIP
    elif data == "get_vip":
        keyboard = []
        for days, cost in VIP_PACKAGES.items():
            keyboard.append([InlineKeyboardButton(
                f"{days} Day{'s' if days > 1 else ''} - {cost} 💎",
                callback_data=f"buy_vip_{days}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⭐ **Get VIP Status**\n\n"
            f"💎 Your diamonds: {user.get('diamonds', 0)}\n\n"
            f"Choose a VIP package:",
            reply_markup=reply_markup
        )
    
    # Buy VIP
    elif data.startswith("buy_vip_"):
        days = int(data.split("_")[2])
        cost = VIP_PACKAGES[days]
        
        if user.get('diamonds', 0) >= cost:
            deduct_diamonds(user_id, cost)
            add_vip_days(user_id, days)
            
            await query.edit_message_text(
                f"🎉 **VIP Activated!**\n\n"
                f"⭐ VIP for {days} day{'s' if days > 1 else ''}\n"
                f"💎 -{cost} diamonds\n"
                f"💰 Remaining: {user.get('diamonds', 0) - cost} diamonds\n\n"
                f"✨ Enjoy your VIP features!"
            )
        else:
            await query.edit_message_text(
                f"❌ **Insufficient Diamonds**\n\n"
                f"💎 Required: {cost}\n"
                f"💰 You have: {user.get('diamonds', 0)}\n"
                f"📈 Need: {cost - user.get('diamonds', 0)} more diamonds\n\n"
                f"🎁 Use /bonus for daily diamonds!"
            )
    
    # Translate Status
    elif data == "translate_status":
        if not is_vip(user_id):
            await query.edit_message_text(
                "❌ **Translation is a VIP feature!**\n\n"
                "⭐ Get VIP to unlock auto-translation\n"
                "🌍 Chat with people from any country!"
            )
            return
        
        translation_status = user.get('settings', {}).get('translation', False)
        status_text = "🟢 ON" if translation_status else "🔴 OFF"
        
        keyboard = [
            [InlineKeyboardButton("🟢 Turn ON", callback_data="translation_on")],
            [InlineKeyboardButton("🔴 Turn OFF", callback_data="translation_off")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🌐 **Translation Status: {status_text}**\n\n"
            f"💡 Translation Power: {'Enabled' if translation_status else 'Disabled'}\n\n"
            f"When enabled, messages will be automatically\n"
            f"translated to your preferred language!",
            reply_markup=reply_markup
        )
    
    # Translation controls
    elif data == "translation_on":
        if not user.get('settings'):
            user['settings'] = {}
        user['settings']['translation'] = True
        save_user(user_id, user)
        
        await query.edit_message_text(
            "✅ **Translation Enabled!**\n\n"
            "🌍 Messages will now be auto-translated\n"
            "🎯 Based on your language preference"
        )
    
    elif data == "translation_off":
        if not user.get('settings'):
            user['settings'] = {}
        user['settings']['translation'] = False
        save_user(user_id, user)
        
        await query.edit_message_text(
            "❌ **Translation Disabled**\n\n"
            "📝 You'll receive messages in original language"
        )
    
    # Settings
    elif data == "settings":
        vip_emoji = "⭐" if is_vip(user_id) else "🔒"
        
        keyboard = [
            [InlineKeyboardButton("👤 Edit Name", callback_data="edit_name")],
            [InlineKeyboardButton("🚻 Change Gender", callback_data="change_gender")],
            [InlineKeyboardButton("🎂 Update Age", callback_data="update_age")],
            [InlineKeyboardButton("🌍 Language", callback_data="change_language")],
            [InlineKeyboardButton(f"{vip_emoji} VIP Settings", callback_data="vip_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚙️ **Settings Menu**\n\n"
            "Configure your profile and preferences:",
            reply_markup=reply_markup
        )

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all non-command messages."""
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ Please use /start first.")
        return
    
    # Check if user is setting age
    if context.user_data.get('waiting_for_age'):
        try:
            age = int(update.message.text)
            if 18 <= age <= 99:
                user['age'] = age
                save_user(user_id, user)
                context.user_data['waiting_for_age'] = False
                
                await update.message.reply_text(
                    f"✅ Age set to: {age}\n\n"
                    f"🎉 Setup complete! Use /next to start chatting!"
                )
            else:
                await update.message.reply_text("❌ Please enter an age between 18 and 99.")
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number.")
        return
    
    if user.get('banned'):
        await update.message.reply_text("❌ You are banned from using this bot.")
        return
    
    partner_id = user.get('partner')
    if not partner_id:
        await update.message.reply_text(
            "❌ You're not connected to anyone.\n"
            "🔍 Use /next to find a chat partner!"
        )
        return
    
    # Forward message to partner
    try:
        message_text = update.message.text or update.message.caption or ""
        
        # Log the message
        log_message(user_id, partner_id, "text", message_text)
        
        # Check for translation
        if message_text:
            translated_text, was_translated = get_translated_message(user_id, partner_id, message_text)
            
            if update.message.text:
                await context.bot.send_message(partner_id, translated_text)
            elif update.message.photo:
                await context.bot.send_photo(
                    partner_id, 
                    update.message.photo[-1].file_id,
                    caption=translated_text
                )
            elif update.message.voice:
                await context.bot.send_voice(
                    partner_id,
                    update.message.voice.file_id,
                    caption=translated_text
                )
            elif update.message.sticker:
                await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
                if translated_text:
                    await context.bot.send_message(partner_id, translated_text)
        else:
            # Forward non-text messages
            if update.message.photo:
                await context.bot.send_photo(partner_id, update.message.photo[-1].file_id)
            elif update.message.voice:
                await context.bot.send_voice(partner_id, update.message.voice.file_id)
            elif update.message.sticker:
                await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
            elif update.message.document:
                await context.bot.send_document(partner_id, update.message.document.file_id)
            elif update.message.video:
                await context.bot.send_video(partner_id, update.message.video.file_id)
            elif update.message.audio:
                await context.bot.send_audio(partner_id, update.message.audio.file_id)
            
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        # Partner might have blocked the bot or left
        disconnect_user(user_id)
        await update.message.reply_text(
            "💔 Connection lost. Your partner may have left.\n"
            "🔍 Use /next to find a new partner!"
        )

# Admin Commands

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user (Admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /ban <user_id>")
        return
    
    try:
        target_id = int(context.args[0])
        user = get_user(target_id)
        
        if not user:
            await update.message.reply_text("❌ User not found.")
            return
        
        user['banned'] = True
        save_user(target_id, user)
        
        # Disconnect user if in chat
        disconnect_user(target_id)
        
        await update.message.reply_text(f"✅ User {target_id} has been banned.")
        
        # Notify user
        try:
            await context.bot.send_message(
                target_id,
                "🚫 You have been banned from the bot for violating community rules."
            )
        except:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user (Admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /unban <user_id>")
        return
    
    try:
        target_id = int(context.args[0])
        user = get_user(target_id)
        
        if not user:
            await update.message.reply_text("❌ User not found.")
            return
        
        user['banned'] = False
        save_user(target_id, user)
        
        await update.message.reply_text(f"✅ User {target_id} has been unbanned.")
        
        # Notify user
        try:
            await context.bot.send_message(
                target_id,
                "🎉 You have been unbanned! You can now use the bot again."
            )
        except:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics (Admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    stats = get_stats()
    
    stats_text = f"""
📊 **Bot Statistics**

👥 Total Users: {stats['total_users']}
💬 Active Chats: {stats['active_chats']}
⏳ Waiting Users: {stats['waiting_users']}
⭐ VIP Users: {stats['vip_users']}
🚫 Banned Users: {stats['banned_users']}
🚨 Total Complaints: {stats['total_complaints']}
"""
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users (Admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /broadcast <message>")
        return
    
    message = " ".join(context.args)
    users = load_users()
    
    sent = 0
    failed = 0
    
    for user_id in users.keys():
        try:
            await context.bot.send_message(int(user_id), f"📢 **Admin Broadcast**\n\n{message}", parse_mode=ParseMode.MARKDOWN)
            sent += 1
        except:
            failed += 1
    
    await update.message.reply_text(
        f"📢 Broadcast complete!\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

async def give_diamonds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give diamonds to a user (Admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text("❌ Usage: /give_diamonds <user_id> <amount>")
        return
    
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        
        user = get_user(target_id)
        if not user:
            await update.message.reply_text("❌ User not found.")
            return
        
        add_diamonds(target_id, amount)
        
        await update.message.reply_text(f"✅ Gave {amount} 💎 to user {target_id}")
        
        # Notify user
        try:
            await context.bot.send_message(
                target_id,
                f"🎁 You received {amount} 💎 diamonds from admin!\n"
                f"💰 Total: {user.get('diamonds', 0) + amount} 💎"
            )
        except:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID or amount.")

async def view_chats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View chat logs (Admin only)."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return
    
    chat_logs = load_chat_logs()
    
    if not chat_logs:
        await update.message.reply_text("📭 No chat logs available.")
        return
    
    logs_text = "📋 **Recent Chat Logs**\n\n"
    
    for chat_key, messages in list(chat_logs.items())[-5:]:  # Last 5 chats
        logs_text += f"**Chat: {chat_key}**\n"
        for msg in messages[-3:]:  # Last 3 messages per chat
            timestamp = msg['timestamp'][:19]
            from_user = msg['from_user']
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            logs_text += f"[{timestamp}] {from_user}: {content}\n"
        logs_text += "\n"
    
    if len(logs_text) > 4000:
        logs_text = logs_text[:4000] + "...\n\n📝 Showing recent logs only."
    
    await update.message.reply_text(logs_text, parse_mode=ParseMode.MARKDOWN)
