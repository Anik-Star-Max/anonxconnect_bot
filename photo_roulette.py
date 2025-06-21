from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import database as db
import config
import random

async def add_photo(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Get highest quality photo
    
    if db.add_photo(user_id, photo.file_id):
        await update.message.reply_text("✅ Photo added to roulette!\n\n"
                                       f"Earn {config.PHOTO_LIKE_REWARD} 💎 per like")
    else:
        await update.message.reply_text("❌ You've reached the maximum number of photos")

async def browse_photos(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get random photo
    all_photos = []
    for user_id, photos in db.photos.items():
        for idx, photo in enumerate(photos):
            all_photos.append((user_id, idx, photo))
    
    if not all_photos:
        await query.edit_message_text("No photos available in roulette yet")
        return
    
    random_photo = random.choice(all_photos)
    photo_user_id, photo_idx, photo_data = random_photo
    photo_user = db.get_user(photo_user_id)
    
    keyboard = [
        [InlineKeyboardButton("❤️ Like Photo", callback_data=f'like_photo_{photo_user_id}_{photo_idx}')],
        [InlineKeyboardButton("🔄 Next Photo", callback_data='browse_photos')],
        [InlineKeyboardButton("🔙 Back", callback_data='photo_roulette')]
    ]
    
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=photo_data['id'],
        caption=f"Photo by: {photo_user.get('name') if photo_user else 'Anonymous'}\n"
                f"Likes: {photo_data.get('likes', 0)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.message.delete()

async def like_photo(update: Update, context: CallbackContext):
    query = update.callback_query
    _, photo_user_id, photo_idx = query.data.split('_')
    photo_idx = int(photo_idx)
    
    if db.like_photo(photo_user_id, photo_idx):
        await query.answer("❤️ Liked! +50 💎 to the owner")
    else:
        await query.answer("❌ Could not like photo")
    
    # Show next photo
    await browse_photos(update, context)
