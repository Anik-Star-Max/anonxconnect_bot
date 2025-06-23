from telegram.ext import CommandHandler, ContextTypes
from config import ADMIN_ID
from database import (
    ban_user, unban_user, get_stats, assign_vip_user,
    give_diamonds_user, get_complaints, get_chat_log
)

def admin_only(func):
    async def wrapper(update, context):
        if str(update.effective_user.id) != ADMIN_ID:
            await update.message.reply_text("You are not authorized.")
            return
        await func(update, context)
    return wrapper

@admin_only
async def ban(update, context):
    if context.args:
        ban_user(int(context.args[0]))
        await update.message.reply_text("User banned.")
    else:
        await update.message.reply_text("Usage: /ban <user_id>")

@admin_only
async def unban(update, context):
    if context.args:
        unban_user(int(context.args[0]))
        await update.message.reply_text("User unbanned.")
    else:
        await update.message.reply_text("Usage: /unban <user_id>")

@admin_only
async def stats(update, context):
    await update.message.reply_text(get_stats())

@admin_only
async def broadcast(update, context):
    if context.args:
        message = " ".join(context.args)
        await update.message.reply_text("Broadcast sent! (Implementation needed)")
    else:
        await update.message.reply_text("Usage: /broadcast <message>")

@admin_only
async def assign_vip(update, context):
    if len(context.args) >= 2:
        assign_vip_user(int(context.args[0]), int(context.args[1]))
        await update.message.reply_text("VIP Assigned.")
    else:
        await update.message.reply_text("Usage: /assign_vip <user_id> <days>")

@admin_only
async def give_diamonds(update, context):
    if len(context.args) >= 2:
        give_diamonds_user(int(context.args[0]), int(context.args[1]))
        await update.message.reply_text("Diamonds given.")
    else:
        await update.message.reply_text("Usage: /give_diamonds <user_id> <amount>")

@admin_only
async def view_complaints(update, context):
    await update.message.reply_text(get_complaints())

@admin_only
async def see_chat(update, context):
    if context.args:
        chat_log = get_chat_log(int(context.args[0]))
        await update.message.reply_text(chat_log)
    else:
        await update.message.reply_text("Usage: /see_chat <user_id>")

def register_admin_handlers(app):
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("assign_vip", assign_vip))
    app.add_handler(CommandHandler("give_diamonds", give_diamonds))
    app.add_handler(CommandHandler("view_complaints", view_complaints))
    app.add_handler(CommandHandler("see_chat", see_chat))
