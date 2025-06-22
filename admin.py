from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
from datetime import datetime, timedelta
from database import get_user_data, save_user_data, get_all_users, ban_user, unban_user
from config import ADMIN_ID

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin control panel"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Access denied! You are not authorized.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Bot Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
        [InlineKeyboardButton("💎 Give Diamonds", callback_data="admin_diamonds")],
        [InlineKeyboardButton("👑 Give VIP", callback_data="admin_vip")],
        [InlineKeyboardButton("🔨 Ban User", callback_data="admin_ban")],
        [InlineKeyboardButton("🚪 Unban User", callback_data="admin_unban")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚨 View Complaints", callback_data="admin_complaints")],
        [InlineKeyboardButton("💬 View User Chats", callback_data="admin_chats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 **Admin Control Panel**\n\n"
        "Choose an option to manage the bot:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    try:
        users = get_all_users()
        total_users = len(users)
        active_users = len([u for u in users.values() if u.get('active', False)])
        vip_users = len([u for u in users.values() if u.get('vip_expires') and 
                        datetime.fromisoformat(u['vip_expires']) > datetime.now()])
        banned_users = len([u for u in users.values() if u.get('banned', False)])
        
        # Load complaints
        try:
            with open('complaints.json', 'r') as f:
                complaints = json.load(f)
            total_complaints = len(complaints)
        except:
            total_complaints = 0
        
        stats_text = f"""
📊 **Bot Statistics**

👥 Total Users: `{total_users}`
🟢 Active Users: `{active_users}`
👑 VIP Users: `{vip_users}`
🔨 Banned Users: `{banned_users}`
🚨 Total Complaints: `{total_complaints}`

📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.callback_query.edit_message_text(
            stats_text,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.callback_query.edit_message_text(f"❌ Error loading stats: {str(e)}")

async def give_diamonds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give diamonds to a user"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/give_diamonds <user_id> <amount>`\n"
            "Example: `/give_diamonds 123456789 1000`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        amount = int(context.args[1])
        
        user_data = get_user_data(target_user_id)
        if not user_data:
            await update.message.reply_text("❌ User not found!")
            return
        
        current_diamonds = user_data.get('diamonds', 0)
        user_data['diamonds'] = current_diamonds + amount
        save_user_data(target_user_id, user_data)
        
        await update.message.reply_text(
            f"✅ Successfully gave {amount} 💎 diamonds to user {target_user_id}\n"
            f"Their new balance: {user_data['diamonds']} 💎"
        )
        
        # Notify the user
        try:
            await context.bot.send_message(
                target_user_id,
                f"🎉 You received {amount} 💎 diamonds from admin!\n"
                f"Your new balance: {user_data['diamonds']} 💎"
            )
        except:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID or amount!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def give_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Give VIP status to a user"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/give_vip <user_id> <days>`\n"
            "Example: `/give_vip 123456789 30`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        days = int(context.args[1])
        
        user_data = get_user_data(target_user_id)
        if not user_data:
            await update.message.reply_text("❌ User not found!")
            return
        
        # Calculate VIP expiry
        current_vip = user_data.get('vip_expires')
        if current_vip and datetime.fromisoformat(current_vip) > datetime.now():
            # Extend existing VIP
            expiry_date = datetime.fromisoformat(current_vip) + timedelta(days=days)
        else:
            # New VIP
            expiry_date = datetime.now() + timedelta(days=days)
        
        user_data['vip_expires'] = expiry_date.isoformat()
        save_user_data(target_user_id, user_data)
        
        await update.message.reply_text(
            f"✅ Successfully gave {days} days VIP to user {target_user_id}\n"
            f"VIP expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Notify the user
        try:
            await context.bot.send_message(
                target_user_id,
                f"🎉 You received {days} days of VIP status from admin!\n"
                f"👑 VIP expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except:
            pass
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID or days!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/ban <user_id> [reason]`\n"
            "Example: `/ban 123456789 Spam`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided"
        
        if ban_user(target_user_id, reason):
            await update.message.reply_text(f"✅ User {target_user_id} has been banned.\nReason: {reason}")
            
            # Notify the user
            try:
                await context.bot.send_message(
                    target_user_id,
                    f"🔨 You have been banned from the bot.\nReason: {reason}\n\n"
                    f"If you think this is a mistake, contact support."
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ User not found!")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/unban <user_id>`\n"
            "Example: `/unban 123456789`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        if unban_user(target_user_id):
            await update.message.reply_text(f"✅ User {target_user_id} has been unbanned.")
            
            # Notify the user
            try:
                await context.bot.send_message(
                    target_user_id,
                    "🎉 You have been unbanned! You can now use the bot again."
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ User not found!")
            
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/broadcast <message>`\n"
            "Example: `/broadcast Hello everyone!`"
        )
        return
    
    message = " ".join(context.args)
    users = get_all_users()
    
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text("📢 Broadcasting message...")
    
    for user_id in users.keys():
        try:
            await context.bot.send_message(
                int(user_id),
                f"📢 **Admin Broadcast**\n\n{message}",
                parse_mode='Markdown'
            )
            sent += 1
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ Broadcast completed!\n"
        f"📤 Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

async def view_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View user complaints"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    try:
        with open('complaints.json', 'r') as f:
            complaints = json.load(f)
        
        if not complaints:
            await update.message.reply_text("📋 No complaints found.")
            return
        
        # Show latest 10 complaints
        recent_complaints = list(complaints.items())[-10:]
        
        text = "🚨 **Recent Complaints:**\n\n"
        for complaint_id, complaint in recent_complaints:
            text += f"**ID:** `{complaint_id}`\n"
            text += f"**From:** `{complaint['reporter_id']}`\n"
            text += f"**Against:** `{complaint['reported_user']}`\n"
            text += f"**Reason:** {complaint['reason']}\n"
            text += f"**Time:** {complaint['timestamp']}\n"
            text += "─" * 30 + "\n\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except FileNotFoundError:
        await update.message.reply_text("📋 No complaints file found.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error loading complaints: {str(e)}")

# Chat monitoring functions
chat_logs = {}

def log_chat_message(sender_id, receiver_id, message):
    """Log chat messages for admin monitoring"""
    if sender_id not in chat_logs:
        chat_logs[sender_id] = []
    
    chat_logs[sender_id].append({
        'timestamp': datetime.now().isoformat(),
        'to': receiver_id,
        'message': message[:100] + "..." if len(message) > 100 else message
    })
    
    # Keep only last 50 messages per user
    if len(chat_logs[sender_id]) > 50:
        chat_logs[sender_id] = chat_logs[sender_id][-50:]

async def view_user_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View user chat logs (admin only)"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/view_chats <user_id>`\n"
            "Example: `/view_chats 123456789`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        if str(target_user_id) not in chat_logs:
            await update.message.reply_text("📭 No chat logs found for this user.")
            return
        
        logs = chat_logs[str(target_user_id)][-20:]  # Last 20 messages
        
        text = f"💬 **Chat Logs for User {target_user_id}:**\n\n"
        for log in logs:
            text += f"**Time:** {log['timestamp'][:19]}\n"
            text += f"**To:** `{log['to']}`\n"
            text += f"**Message:** {log['message']}\n"
            text += "─" * 25 + "\n\n"
        
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")
