import json
import os
from datetime import datetime
from database import get_user, save_user, load_users, save_users

def add_photo_to_roulette(user_id, photo_file_id, photo_type="profile"):
    """Add a photo to user's photo roulette."""
    user = get_user(user_id)
    if not user:
        return False
    
    if 'profile_photos' not in user:
        user['profile_photos'] = []
    
    # Check if user already has max photos
    if len(user['profile_photos']) >= 5:  # Max 5 photos per user
        return False
    
    photo_data = {
        'file_id': photo_file_id,
        'type': photo_type,
        'uploaded': datetime.now().isoformat(),
        'likes': 0,
        'dislikes': 0,
        'views': 0
    }
    
    user['profile_photos'].append(photo_data)
    save_user(user_id, user)
    return True

def get_random_photo():
    """Get a random photo from photo roulette."""
    users = load_users()
    all_photos = []
    
    for user_id, user_data in users.items():
        if user_data.get('profile_photos'):
            for i, photo in enumerate(user_data['profile_photos']):
                all_photos.append({
                    'user_id': int(user_id),
                    'photo_index': i,
                    'photo_data': photo,
                    'user_name': user_data.get('first_name', 'Anonymous'),
                    'user_age': user_data.get('age'),
                    'user_gender': user_data.get('gender')
                })
    
    if not all_photos:
        return None
    
    # Sort by VIP status and recent uploads for better distribution
    import random
    random.shuffle(all_photos)
    return all_photos[0] if all_photos else None

def rate_photo(user_id, photo_owner_id, photo_index, rating):
    """Rate a photo (like/dislike)."""
    user = get_user(photo_owner_id)
    if not user or not user.get('profile_photos'):
        return False
    
    if photo_index >= len(user['profile_photos']):
        return False
    
    photo = user['profile_photos'][photo_index]
    
    # Increment view count
    photo['views'] = photo.get('views', 0) + 1
    
    # Add rating
    if rating == 'like':
        photo['likes'] = photo.get('likes', 0) + 1
        # Give diamonds to photo owner
        from database import add_diamonds
        add_diamonds(photo_owner_id, 5)  # 5 diamonds per like
        
        # Update user's total photo likes
        user['photo_likes'] = user.get('photo_likes', 0) + 1
    elif rating == 'dislike':
        photo['dislikes'] = photo.get('dislikes', 0) + 1
    
    save_user(photo_owner_id, user)
    return True

def get_user_photo_stats(user_id):
    """Get user's photo statistics."""
    user = get_user(user_id)
    if not user:
        return None
    
    photos = user.get('profile_photos', [])
    total_likes = sum(p.get('likes', 0) for p in photos)
    total_views = sum(p.get('views', 0) for p in photos)
    total_dislikes = sum(p.get('dislikes', 0) for p in photos)
    
    return {
        'total_photos': len(photos),
        'total_likes': total_likes,
        'total_views': total_views,
        'total_dislikes': total_dislikes,
        'photos': photos
    }

def delete_photo(user_id, photo_index):
    """Delete a photo from user's roulette."""
    user = get_user(user_id)
    if not user or not user.get('profile_photos'):
        return False
    
    if photo_index >= len(user['profile_photos']):
        return False
    
    user['profile_photos'].pop(photo_index)
    save_user(user_id, user)
    return True
