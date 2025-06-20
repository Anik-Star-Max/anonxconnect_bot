# anonx_bot_system/main.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os, json, datetime, random
from deep_translator import GoogleTranslator

DATA_FILE = "user_data.json"
TOKEN = os.environ.get("BOT_TOKEN")

ADMIN_ID = 5249331417  # @mysteryman02 user ID

# Load or initialize user database
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump({}, f)
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

users = load_data()
pending_settings = {}
pending_ratings = {}
active_chats = {}
waiting_list = []

INTEREST_OPTIONS = ["📚 Books", "🎮 Games", "💞 Romance", "🍿 Anime", "🧠 Psychology", "🔥 Private"]
SETTINGS_OPTIONS = ["Country 🌍", "Gender 🚻", "Age 🎂", "Interests 🎯", "Distance 📍", "Language 🌐", "Back ⬅️"]
LANGUAGES = ["English", "Hindi", "Bengali", "Tamil", "Telugu", "Spanish", "German", "French", "Arabic", "Russian", "Indonesian"]

LANG_CODES = {
    "English": "en", "Hindi": "hi", "Bengali": "bn", "Tamil": "ta", "Telugu": "te",
    "Spanish": "es", "German": "de", "French": "fr", "Arabic": "ar", "Russian": "ru", "Indonesian": "id"
}

MESSAGES = {
    "welcome_new": {
        "en": "👤 Profile created! Use /menu to begin. Your name: {name}",
        "hi": "👤 प्रोफ़ाइल बन गई! शुरू करने के लिए /menu का उपयोग करें। आपका नाम: {name}",
        "bn": "👤 প্রোফাইল তৈরি হয়েছে! শুরু করতে /menu ব্যবহার করুন। আপনার নাম: {name}",
        "es": "👤 ¡Perfil creado! Usa /menu para comenzar. Tu nombre: {name}",
        "de": "👤 Profil erstellt! Benutze /menu, um zu beginnen. Dein Name: {name}",
        "fr": "👤 Profil créé ! Utilisez /menu pour commencer. Votre nom : {name}",
        "ar": "👤 تم إنشاء الملف الشخصي! استخدم /menu للبدء. اسمك: {name}",
        "ru": "👤 Профиль создан! Используйте /menu для начала. Ваше имя: {name}",
        "id": "👤 Profil dibuat! Gunakan /menu untuk memulai. Nama Anda: {name}"
    },
    "welcome_back": {
        "en": "👋 Welcome back! Use /menu to explore features.",
        "hi": "👋 वापसी पर स्वागत है! सुविधाओं को देखने के लिए /menu का उपयोग करें।",
        "bn": "👋 আবার স্বাগতম! বৈশিষ্ট্যগুলি দেখতে /menu ব্যবহার করুন।",
        "es": "👋 ¡Bienvenido de nuevo! Usa /menu para explorar las funciones.",
        "de": "👋 Willkommen zurück! Benutze /menu, um die Funktionen zu entdecken.",
        "fr": "👋 Bon retour ! Utilisez /menu pour explorer les fonctionnalités.",
        "ar": "👋 مرحبًا بعودتك! استخدم /menu لاستكشاف الميزات.",
        "ru": "👋 С возвращением! Используйте /menu, чтобы изучить функции.",
        "id": "👋 Selamat datang kembali! Gunakan /menu untuk menjelajahi fitur."
    },
    "choose_language": {
        "en": "🌐 Choose your language:",
        "hi": "🌐 अपनी भाषा चुनें:",
        "bn": "🌐 আপনার ভাষা নির্বাচন করুন:",
        "es": "🌐 Elige tu idioma:",
        "de": "🌐 Wähle deine Sprache:",
        "fr": "🌐 Choisissez votre langue :",
        "ar": "🌐 اختر لغتك:",
        "ru": "🌐 Выберите ваш язык:",
        "id": "🌐 Pilih bahasa Anda:"
    },
    "language_set": {
        "en": "✅ Language set to {lang}.",
        "hi": "✅ भाषा {lang} पर सेट हो गई है।",
        "bn": "✅ ভাষা {lang} এ সেট করা হয়েছে।",
        "es": "✅ Idioma establecido en {lang}.",
        "de": "✅ Sprache auf {lang} gesetzt.",
        "fr": "✅ Langue définie sur {lang}.",
        "ar": "✅ تم تعيين اللغة إلى {lang}.",
        "ru": "✅ Язык установлен на {lang}.",
        "id": "✅ Bahasa diatur ke {lang}."
    }
}

def translate(user_id, key, **kwargs):
    user = users.get(str(user_id), {})
    lang = user.get("language", "English")
    code = LANG_CODES.get(lang, "en")
    text = MESSAGES.get(key, {}).get(code, MESSAGES.get(key, {}).get("en", ""))
    return text.format(**kwargs)

def auto_translate(text, source_lang, target_lang):
    try:
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except:
        return text

def create_profile(user_id):
    now = datetime.datetime.utcnow().isoformat()
    anon_name = f"anon_{str(user_id)[-4:]}"
    users[str(user_id)] = {
        "anon_name": anon_name,
        "points": 0,
        "vip": False,
        "vip_expiry": "",
        "last_reward": "",
        "language": "English",
        "partner": None,
        "rating": 5,
        "joined": now,
        "interests": [],
        "gender": "", "age": "", "country": "", "distance": "",
        "referrals": 0, "ref_code": str(user_id)
    }
    save_data(users)
    return anon_name

def check_vip_expiry(user_id):
    u = users.get(str(user_id))
    if u and u.get("vip") and u.get("vip_expiry"):
        expiry = datetime.datetime.fromisoformat(u["vip_expiry"])
        if datetime.datetime.utcnow() > expiry:
            u["vip"] = False
            u["vip_expiry"] = ""
            save_data(users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    is_new = str(user_id) not in users
    if is_new:
        anon_name = create_profile(user_id)
        if args:
            ref = args[0]
            if ref != str(user_id) and ref in users:
                users[ref]["points"] += 5
                users[ref]["referrals"] += 1
                save_data(users)
        message = translate(user_id, "welcome_new", name=anon_name)
    else:
        message = translate(user_id, "welcome_back")

    await update.message.reply_text(message)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎯 Referral", callback_data="menu_ref"), InlineKeyboardButton("🏆 Leaderboard", callback_data="menu_leader")],
        [InlineKeyboardButton("📸 Photo Roulette", callback_data="menu_photo"), InlineKeyboardButton("💠 VIP Features", callback_data="menu_premium")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")]
    ]
    await update.message.reply_text("📋 *Main Menu:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    setting = query.data.replace("setting_", "")
    if setting == "back":
        await menu(update, context)
        return

    if setting == "language":
        keyboard = [[InlineKeyboardButton(lang, callback_data=f"lang_{lang}")] for lang in LANGUAGES]
        await query.message.reply_text(translate(user_id, "choose_language"), reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        pending_settings[user_id] = setting
        await query.message.reply_text(f"✍️ Please type your {setting}.")
    await query.answer()

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = query.data.replace("lang_", "")
    users[user_id]["language"] = lang
    save_data(users)
    await query.message.reply_text(translate(user_id, "language_set", lang=lang))
    await query.answer()

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users.get(str(user_id))
    referral_link = f"https://t.me/anonxconnect_bot?start={user['ref_code']}"
    await update.message.reply_text(f"🔗 Your referral link:\n{referral_link}\n\nYou’ve referred: {user['referrals']} users")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("points", 0), reverse=True)
    text = "🏆 Top Referrals & Points:\n"
    for i, (uid, info) in enumerate(sorted_users[:10], start=1):
        text += f"{i}. {info['anon_name']} - {info['points']} pts\n"
    await update.message.reply_text(text)

async def photo_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Coming soon! You'll be able to share and guess photos anonymously.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("photo", photo_roulette))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^setting_"))
    app.add_handler(CallbackQueryHandler(set_language, pattern="^lang_"))

    app.run_polling()
