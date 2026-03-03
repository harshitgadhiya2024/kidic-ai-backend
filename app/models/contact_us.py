"""Contact Us database model"""

from datetime import datetime


class ContactUsModel:
    """Contact Us model representing the contact_us collection structure"""

    COLLECTION_NAME = "contact_us"

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"

    @staticmethod
    def create_contact_document(
        user_id: str,
        message: str,
        subject: str,
    ) -> dict:
        """Create a new contact us document"""
        now = datetime.utcnow()
        return {
            "user_id": user_id,
            "message": message,
            "subject": subject,
            "status": ContactUsModel.STATUS_PENDING,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def serialize_contact(contact_doc: dict) -> dict:
        """Serialize contact us document for API response"""
        if not contact_doc:
            return None

        contact_doc["id"] = str(contact_doc.pop("_id"))
        contact_doc["created_at"] = contact_doc["created_at"].isoformat() if contact_doc.get("created_at") else None
        contact_doc["updated_at"] = contact_doc["updated_at"].isoformat() if contact_doc.get("updated_at") else None

        return contact_doc
