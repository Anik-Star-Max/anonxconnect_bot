from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
import database

async def admin_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🔒 This command is for the admin only.")
        return

    msg = update.message.text.strip().lower()
    if msg.startswith("/ban"):
        parts = msg.split()
        if len(parts) < 2:
            await update.message.reply_text("Usage: /ban <user_id>")
            return
        user_id = parts[1]
        await ban_user(user_id)
        await update.message.reply_text(f"User {user_id} banned.")
    elif msg.startswith("/unban"):
        parts = msg.split()
        if len(parts) < 2:
            await update.message.reply_text("Usage: /unban <user_id>")
            return
        user_id = parts[1]
        await unban_user(user_id)
        await update.message.reply_text(f"User {user_id} unbanned.")
    elif msg.startswith("/vip"):
        parts = msg.split()
        if len(parts) < 3:
            await update.message.reply_text("Usage: /vip <user_id> <days>")
            return
        user_id, days = parts[1], int(parts[2])
        await give_vip(user_id, days)
        await update.message.reply_text(f"Gave VIP for {days} days to {user_id}.")
    elif msg.startswith("/diamond"):
        parts = msg.split()
        if len(parts) < 3:
            await update.message.reply_text("Usage: /diamond <user_id> <amount>")
            return
        user_id, amount = parts[1], int(parts[2])
        await give_diamonds(user_id, amount)
        await update.message.reply_text(f"Gave {amount} diamonds to {user_id}.")
    else:
        await update.message.reply_text("Admin commands: /ban /unban /vip /diamond")

async def ban_user(user_id):
    users = database._load_users()
    if user_id in users:
        users[user_id]["banned"] = True
        database._save_users(users)

async def unban_user(user_id):
    users = database._load_users()
    if user_id in users:
        users[user_id]["banned"] = False
        database._save_users(users)

async def give_vip(user_id, days):
    from datetime import datetime, timedelta
    users = database._load_users()
    if user_id in users:
        now = datetime.now()
        old = users[user_id].get("vip_until")
        if old:
            now = max(now, datetime.fromisoformat(old))
        users[user_id]["vip_until"] = (now + timedelta(days=days)).isoformat()
        database._save_users(users)

async def give_diamonds(user_id, amount):
    users = database._load_users()
    if user_id in users:
        users[user_id]["diamonds"] = users[user_id].get("diamonds", 0) + amount
        database._save_users(users)
