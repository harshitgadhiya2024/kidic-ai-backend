"""Photoshoot Generation database model"""

from datetime import datetime
from typing import Optional


class PhotoshootGenerationModel:
    """Photoshoot Generation model representing the photoshoot_generations collection structure"""
    
    COLLECTION_NAME = "photoshoot_generations"
    
    # Status constants
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    # Model constants
    MODEL_SEEDDREAM = "seeddream"
    MODEL_GEMINI = "gemini"

    @staticmethod
    def create_generation_document(
        user_id: str,
        template_id: str,
        kid_image_url: str,
        task_id: Optional[str] = None,
        status: str = STATUS_PENDING,
    ) -> dict:
        """Create a new photoshoot generation document"""
        now = datetime.utcnow()
        return {
            "user_id": user_id,
            "template_id": template_id,
            "kid_image_url": kid_image_url,
            "task_id": task_id,
            "is_favorite": False,
            "model_used": None,
            "status": status,
            "result_url": None,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
        }
    
    @staticmethod
    def update_generation_document(**kwargs) -> dict:
        """Create an update document for photoshoot generation"""
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        return {"$set": update_data}
    
    @staticmethod
    def mark_as_processing(task_id: str) -> dict:
        """Create an update document to mark generation as processing"""
        return {
            "$set": {
                "status": PhotoshootGenerationModel.STATUS_PROCESSING,
                "task_id": task_id,
                "updated_at": datetime.utcnow()
            }
        }
    
    @staticmethod
    def mark_as_completed(result_url: str, model_used: Optional[str] = None) -> dict:
        """Create an update document to mark generation as completed"""
        return {
            "$set": {
                "status": PhotoshootGenerationModel.STATUS_COMPLETED,
                "result_url": result_url,
                "model_used": model_used,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    
    @staticmethod
    def mark_as_favorite() -> dict:
        """Create an update document to mark generation as favourite"""
        return {
            "$set": {
                "is_favorite": True,
                "updated_at": datetime.utcnow()
            }
        }

    @staticmethod
    def mark_as_unfavorite() -> dict:
        """Create an update document to unmark generation as favourite"""
        return {
            "$set": {
                "is_favorite": False,
                "updated_at": datetime.utcnow()
            }
        }

    @staticmethod
    def mark_as_failed(error_message: str) -> dict:
        """Create an update document to mark generation as failed"""
        return {
            "$set": {
                "status": PhotoshootGenerationModel.STATUS_FAILED,
                "error_message": error_message,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    
    @staticmethod
    def serialize_generation(generation_doc: dict) -> dict:
        """Serialize photoshoot generation document for API response"""
        if not generation_doc:
            return None
        
        generation_doc["id"] = str(generation_doc.pop("_id"))
        generation_doc["created_at"] = generation_doc["created_at"].isoformat() if generation_doc.get("created_at") else None
        generation_doc["updated_at"] = generation_doc["updated_at"].isoformat() if generation_doc.get("updated_at") else None
        generation_doc["completed_at"] = generation_doc["completed_at"].isoformat() if generation_doc.get("completed_at") else None
        
        return generation_doc

