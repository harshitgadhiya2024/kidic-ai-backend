"""OTP database model"""

from datetime import datetime, timedelta
from typing import Optional


class OTPModel:
    """OTP model representing the otps collection structure"""
    
    COLLECTION_NAME = "otps"
    
    @staticmethod
    def create_otp_document(
        email: str,
        otp_code: str,
        expire_minutes: int = 10
    ) -> dict:
        """Create a new OTP document"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=expire_minutes)
        
        return {
            "email": email.lower(),
            "otp_code": otp_code,
            "expires_at": expires_at,
            "is_used": False,
            "created_at": now,
        }
    
    @staticmethod
    def mark_as_used() -> dict:
        """Create an update document to mark OTP as used"""
        return {"$set": {"is_used": True}}
    
    @staticmethod
    def is_valid(otp_doc: dict) -> bool:
        """Check if OTP is valid (not used and not expired)"""
        if not otp_doc:
            return False
        
        if otp_doc.get("is_used", False):
            return False
        
        expires_at = otp_doc.get("expires_at")
        if not expires_at:
            return False
        
        return datetime.utcnow() < expires_at
