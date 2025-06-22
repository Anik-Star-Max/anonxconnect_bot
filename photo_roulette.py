import json
import random
from datetime import datetime
from database import load_users, save_users

class PhotoRoulette:
    def __init__(self):
        self.photos_file = "photo_roulette.json"
        self.photos_data = {
            "photos": {},
            "likes": {},
            "views": {}
        }
        self.load_photos()

    def load_photos(self):
        """Load photo roulette data from JSON file"""
        try:
            with open(self.photos_file, 'r', encoding='utf-8') as f:
                self.photos_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.photos_data = {
                "photos": {},
                "likes": {},
                "views": {}
            }

            self.save_photos()
    
    def save_photos(self):
        """Save photo roulette data to JSON file"""
        with open(self.photos_file, 'w', encoding='utf-8') as f:
            json.dump(self.photos_data, f, indent=2, ensure_ascii=False)
    
    def add_photo(self, user_id, photo_file_id, caption=""):
        """Add user photo to roulette"""
        user_id_str = str(user_id)
        self.photos_data["photos"][user_id_str] = {
            "file_id": photo_file_id,
            "caption": caption,
            "upload_date": datetime.now().isoformat(),
            "likes": 0,
            "dislikes": 0,
            "total_views": 0
        }
        
        if user_id_str not in self.photos_data["likes"]:
            self.photos_data["likes"][user_id_str] = []
        
        if user_id_str not in self.photos_data["views"]:
            self.photos_data["views"][user_id_str] = []
        
        self.save_photos()
        return True
    
    def get_random_photo(self, current_user_id):
        """Get random photo for user to rate"""
        current_user_str = str(current_user_id)
        available_photos = []
        
        for user_id, photo_data in self.photos_data["photos"].items():
            # Don't show own photo
            if user_id == current_user_str:
                continue
            
            # Don't show already viewed photos
            if current_user_str in self.photos_data["views"]:
                if user_id in self.photos_data["views"][current_user_str]:
                    continue
            
            available_photos.append((user_id, photo_data))
        
        if not available_photos:
            return None, None
        
        # Select random photo
        selected_user_id, photo_data = random.choice(available_photos)
        
        # Mark as viewed
        if current_user_str not in self.photos_data["views"]:
            self.photos_data["views"][current_user_str] = []
        
        self.photos_data["views"][current_user_str].append(selected_user_id)
        
        # Increment view count
        self.photos_data["photos"][selected_user_id]["total_views"] += 1
        
        self.save_photos()
        
        return selected_user_id, photo_data
    
    def rate_photo(self, rater_user_id, photo_owner_id, is_like=True):
        """Rate a photo (like or dislike)"""
        rater_str = str(rater_user_id)
        owner_str = str(photo_owner_id)
        
        # Check if already rated
        if rater_str in self.photos_data["likes"]:
            if owner_str in self.photos_data["likes"][rater_str]:
                return False, "Already rated this photo!"
        
        # Add to likes tracking
        if rater_str not in self.photos_data["likes"]:
            self.photos_data["likes"][rater_str] = []
        
        self.photos_data["likes"][rater_str].append(owner_str)
        
        # Update photo stats
        if owner_str in self.photos_data["photos"]:
            if is_like:
                self.photos_data["photos"][owner_str]["likes"] += 1
            else:
                self.photos_data["photos"][owner_str]["dislikes"] += 1
        
        self.save_photos()
        return True, "Rating recorded!"
    
    def get_user_photo_stats(self, user_id):
        """Get user's photo statistics"""
        user_str = str(user_id)
        
        if user_str not in self.photos_data["photos"]:
            return None
        
        photo_data = self.photos_data["photos"][user_str]
        return {
            "likes": photo_data["likes"],
            "dislikes": photo_data["dislikes"],
            "total_views": photo_data["total_views"],
            "upload_date": photo_data["upload_date"]
        }
    
    def remove_user_photo(self, user_id):
        """Remove user's photo from roulette"""
        user_str = str(user_id)
        
        if user_str in self.photos_data["photos"]:
            del self.photos_data["photos"][user_str]
        
        if user_str in self.photos_data["likes"]:
            del self.photos_data["likes"][user_str]
        
        if user_str in self.photos_data["views"]:
            del self.photos_data["views"][user_str]
        
        # Remove from other users' views and likes
        for user_data in self.photos_data["views"].values():
            if user_str in user_data:
                user_data.remove(user_str)
        
        for user_data in self.photos_data["likes"].values():
            if user_str in user_data:
                user_data.remove(user_str)
        
        self.save_photos()
        return True
    
    def get_top_photos(self, limit=10):
        """Get top rated photos"""
        photos_with_scores = []
        
        for user_id, photo_data in self.photos_data["photos"].items():
            score = photo_data["likes"] - photo_data["dislikes"]
            photos_with_scores.append((user_id, photo_data, score))
        
        # Sort by score descending
        photos_with_scores.sort(key=lambda x: x[2], reverse=True)
        
        return photos_with_scores[:limit]

# Global instance
photo_roulette = PhotoRoulette()
