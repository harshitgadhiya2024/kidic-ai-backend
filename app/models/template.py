"""Template database model"""

from datetime import datetime
from typing import Optional


class TemplateModel:
    """Template model representing the templates collection structure"""
    
    COLLECTION_NAME = "templates"
    
    @staticmethod
    def create_template_document(
        main_image_url: str,
        pass_image_url: str,
        pose_details: str,
        cloths_details: str,
        aspect_ratio: str,
    ) -> dict:
        """Create a new template document"""
        now = datetime.utcnow()
        return {
            "main_image_url": main_image_url,
            "pass_image_url": pass_image_url,
            "pose_details": pose_details,
            "cloths_details": cloths_details,
            "aspect_ratio": aspect_ratio,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
    
    @staticmethod
    def update_template_document(**kwargs) -> dict:
        """Create an update document for template"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        return {"$set": update_data}
    
    @staticmethod
    def soft_delete() -> dict:
        """Create an update document to soft delete template"""
        return {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    
    @staticmethod
    def serialize_template(template_doc: dict) -> dict:
        """Serialize template document for API response"""
        if not template_doc:
            return None
        
        template_doc["id"] = str(template_doc.pop("_id"))
        template_doc["created_at"] = template_doc["created_at"].isoformat() if template_doc.get("created_at") else None
        template_doc["updated_at"] = template_doc["updated_at"].isoformat() if template_doc.get("updated_at") else None
        
        return template_doc
