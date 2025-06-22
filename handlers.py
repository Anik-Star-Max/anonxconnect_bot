from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import database
import admin
import translation
import referral
import photo_roulette

MENU_COMMANDS = [
    ("Referral TOP", "referral_top"),
    ("Profile", "profile"),
    ("Rules", "rules"),
    ("Photo Roulette", "photo_roulette"),
    ("Premium", "premium"),
    ("Get Vip status", "get_vip"),
    ("Translate status", "translate_status"),
    ("⚙️ Settings", "settings"),
]

def get_menu_keyboard(user_data):
    buttons = [[InlineKeyboardButton(text, callback_data=data)] for text, data in MENU_COMMANDS]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await database.add_user(user)
    await update.message.reply_text(
        f"🆕 Welcome to Anonymous Chat, {user.first_name}! 🌐\n"
        f"Meet strangers, chat anonymously, and enjoy! Use /menu for all features.",
        reply_markup=get_menu_keyboard(database.get_user_data(user.id))
    )

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = await database.start_next_chat(user_id)
    await update.message.reply_text(msg)

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = await database.stop_current_chat(user_id)
    await update.message.reply_text(msg)
    # Notify partner if needed
    partner_id = database.get_partner_id(user_id)
    if partner_id:
        await context.bot.send_message(partner_id, "🚫 Your partner has left the chat.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        "🔑 Main Menu / Settings\nChoose an option below:",
        reply_markup=get_menu_keyboard(database.get_user_data(user.id))
    )

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = await database.daily_bonus(user_id)
    await update.message.reply_text(msg)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    profile_txt = await database.get_profile(user_id)
    await update.message.reply_text(profile_txt, parse_mode="HTML")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("rules.txt", "r", encoding="utf-8") as f:
        rules_text = f.read()
    await update.message.reply_text(f"💡 Terms of Use:\n\n{rules_text}")

async def referral_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = await referral.get_top()
    await update.message.reply_text(top, parse_mode="HTML")

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 <b>Premium Features</b> 💎\n"
        "- Gender & Age Match\n"
        "- Profile Preview\n"
        "- Photo Roulette\n"
        "- Priority in Matchmaking\n"
        "- Translation Power\n"
        "- VIP Badge\n"
        "- And much more!\n"
        "Get VIP from /get_vip"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def get_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌟 <b>Get VIP Status</b> 🌟\n"
        "1 Day: 500 💎\n"
        "2 Days: 1000 💎\n"
        "3 Days: 1500 💎\n"
        "5 Days: 2000 💎\n"
        "Earn diamonds via referrals, giveaways, or buy directly.\n"
        "Use /bonus for daily diamonds!\n"
        "Contact admin to buy more."
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def translate_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_vip = await database.is_vip(user_id)
    if not is_vip:
        await update.message.reply_text("🔒 Only VIP users can use translation power!")
        return
    status = await database.get_translate_status(user_id)
    on_off = "ON" if status else "OFF"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("On", callback_data="set_translate_on"),
         InlineKeyboardButton("Off", callback_data="set_translate_off")],
    ])
    await update.message.reply_text(
        f"🈳 Translation Power: <b>{on_off}</b>\n"
        "If ON, all messages from other languages will be translated to your chosen language.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    settings_text = await database.get_settings_text(user_id)
    await update.message.reply_text(
        settings_text,
        reply_markup=get_menu_keyboard(database.get_user_data(user_id)),
        parse_mode="HTML"
    )

async def photo_roulette_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = await photo_roulette.menu(user_id)
    await update.message.reply_text(msg)

async def inline_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "referral_top":
        top = await referral.get_top()
        await query.answer()
        await query.edit_message_text(top, parse_mode="HTML")
    elif data == "profile":
        profile_txt = await database.get_profile(user_id)
        await query.answer()
        await query.edit_message_text(profile_txt, parse_mode="HTML")
    elif data == "rules":
        with open("rules.txt", "r", encoding="utf-8") as f:
            rules_text = f.read()
        await query.answer()
        await query.edit_message_text(f"💡 Terms of Use:\n\n{rules_text}")
    elif data == "photo_roulette":
        msg = await photo_roulette.menu(user_id)
        await query.answer()
        await query.edit_message_text(msg)
    elif data == "premium":
        await premium(query, context)
    elif data == "get_vip":
        await get_vip(query, context)
    elif data == "translate_status":
        await translate_status(query, context)
    elif data == "settings":
        settings_text = await database.get_settings_text(user_id)
        await query.answer()
        await query.edit_message_text(settings_text, parse_mode="HTML")
    elif data == "set_translate_on":
        await database.set_translate_status(user_id, True)
        await query.answer("Translation ON")
        await query.edit_message_text("🈳 Translation Power is now <b>ON</b>.", parse_mode="HTML")
    elif data == "set_translate_off":
        await database.set_translate_status(user_id, False)
        await query.answer("Translation OFF")
        await query.edit_message_text("🈳 Translation Power is now <b>OFF</b>.", parse_mode="HTML")
    else:
        await query.answer("Unknown option.", show_alert=True)

async def relay_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not database.is_in_chat(user_id):
        return  # Ignore message if not chatting

    partner_id = database.get_partner_id(user_id)
    if not partner_id:
        return

    # Get translation preference
    user_data = database.get_user_data(user_id)
    partner_data = database.get_user_data(partner_id)
    should_translate = partner_data.get("translate", False)
    from_lang = user_data.get("language", "en")
    to_lang = partner_data.get("language", "en")

    # Text messages
    if update.message.text:
        text = update.message.text
        if should_translate and from_lang != to_lang:
            text = await translation.translate_message(text, from_lang, to_lang)
        await context.bot.send_message(chat_id=partner_id, text=text)
    # Forward other message types
    elif update.message.photo:
        await context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1].file_id, caption=update.message.caption or "")
    elif update.message.sticker:
        await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
    elif update.message.voice:
        await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id)
    elif update.message.document:
        await context.bot.send_document(chat_id=partner_id, document=update.message.document.file_id, caption=update.message.caption or "")

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("next", next_chat))
    app.add_handler(CommandHandler("stop", stop_chat))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("bonus", bonus))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("premium", premium))
    app.add_handler(CommandHandler("get_vip", get_vip))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("photo_roulette", photo_roulette_cmd))
    app.add_handler(CommandHandler("referral_top", referral_top))
    app.add_handler(CallbackQueryHandler(inline_button_handler))
    app.add_handler(MessageHandler(filters.COMMAND, admin.admin_command_handler))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO | filters.STICKER | filters.VOICE | filters.DOCUMENT, relay_message))
