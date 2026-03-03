"""User database model"""

from datetime import datetime
from typing import Optional
from bson import ObjectId


class UserModel:
    """User model representing the users collection structure"""
    
    COLLECTION_NAME = "users"
    
    @staticmethod
    def create_user_document(
        email: str,
        username: str,
        credits: int = 1,
        profile_picture: Optional[str] = None,
    ) -> dict:
        """Create a new user document"""
        now = datetime.utcnow()
        return {
            "email": email.lower(),
            "username": username,
            "profile_picture": profile_picture,
            "credits": credits,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    
    @staticmethod
    def update_user_document(**kwargs) -> dict:
        """Create an update document for user"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        return {"$set": update_data}
    
    @staticmethod
    def serialize_user(user_doc: dict) -> dict:
        """Serialize user document for API response"""
        if not user_doc:
            return None
        
        user_doc["id"] = str(user_doc.pop("_id"))
        user_doc["created_at"] = user_doc["created_at"].isoformat() if user_doc.get("created_at") else None
        user_doc["updated_at"] = user_doc["updated_at"].isoformat() if user_doc.get("updated_at") else None
        
        return user_doc
