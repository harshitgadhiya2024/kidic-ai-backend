"""Authentication service with business logic"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.config import settings
from app.core.security import generate_otp, create_access_token, create_refresh_token
from app.models import UserModel, OTPModel
from app.services.email_service import email_service
from app.utils import generate_username_from_email

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for managing OTP and user authentication"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db[UserModel.COLLECTION_NAME]
        self.otps_collection = db[OTPModel.COLLECTION_NAME]
    
    async def send_otp(self, email: str, background_tasks=None) -> Tuple[bool, str]:
        """
        Generate and send OTP to email
        
        Args:
            email: Email address to send OTP to
            background_tasks: FastAPI BackgroundTasks for async email sending
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            email = email.lower()
            
            # Generate OTP
            otp_code = generate_otp(length=settings.otp_length)
            
            # Create OTP document
            otp_doc = OTPModel.create_otp_document(
                email=email,
                otp_code=otp_code,
                expire_minutes=settings.otp_expire_minutes
            )
            
            # Save OTP to database
            await self.otps_collection.insert_one(otp_doc)
            
            # Get username if user exists
            user = await self.users_collection.find_one({"email": email})
            username = user.get("username", "User") if user else "User"
            
            # Send OTP email in background
            if background_tasks:
                background_tasks.add_task(
                    email_service.send_otp_email,
                    recipient_email=email,
                    otp_code=otp_code,
                    username=username
                )
                logger.info(f"OTP generated and email scheduled in background for {email}")
            else:
                # Fallback to synchronous sending if no background_tasks provided
                email_sent = email_service.send_otp_email(
                    recipient_email=email,
                    otp_code=otp_code,
                    username=username
                )
                if not email_sent:
                    logger.warning(f"Email sending failed for {email}, but OTP is valid")
            
            return True, f"OTP sent successfully to {email}"
            
        except Exception as e:
            logger.error(f"Error sending OTP to {email}: {str(e)}")
            return False, f"Error sending OTP: {str(e)}"
    
    async def verify_otp(self, email: str, otp_code: str) -> Tuple[bool, Optional[str]]:
        """
        Verify OTP code
        
        Args:
            email: Email address
            otp_code: OTP code to verify
            
        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        try:
            email = email.lower()
            
            # Find the most recent OTP for this email
            otp_doc = await self.otps_collection.find_one(
                {"email": email, "otp_code": otp_code, "is_used": False},
                sort=[("created_at", -1)]
            )
            
            if not otp_doc:
                return False, "Invalid OTP code"
            
            # Check if OTP is valid (not expired and not used)
            if not OTPModel.is_valid(otp_doc):
                if otp_doc.get("is_used"):
                    error_msg = "OTP has already been used"
                else:
                    error_msg = "OTP has expired"
                return False, error_msg
            
            # Mark OTP as used
            await self.otps_collection.update_one(
                {"_id": otp_doc["_id"]},
                OTPModel.mark_as_used()
            )
            
            logger.info(f"OTP verified successfully for {email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error verifying OTP for {email}: {str(e)}")
            return False, f"Error verifying OTP: {str(e)}"
    
    async def get_or_create_user(self, email: str) -> dict:
        """
        Get existing user or create new user
        
        Args:
            email: Email address
            
        Returns:
            User document
        """
        try:
            email = email.lower()
            
            # Check if user already exists
            user = await self.users_collection.find_one({"email": email})
            
            if user:
                logger.info(f"Existing user found for {email}")
                return UserModel.serialize_user(user)
            
            # Create new user
            username = generate_username_from_email(email)
            user_doc = UserModel.create_user_document(
                email=email,
                username=username,
                credits=settings.default_user_credits,
                profile_picture=None
            )
            
            result = await self.users_collection.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            
            logger.info(f"New user created for {email}")
            return UserModel.serialize_user(user_doc)
            
        except Exception as e:
            logger.error(f"Error getting/creating user for {email}: {str(e)}")
            raise
    
    async def create_tokens(self, user_id: str) -> dict:
        """
        Create access and refresh tokens for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with access_token and refresh_token
        """
        token_data = {"sub": user_id}
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def authenticate_user(self, email: str, otp_code: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Complete authentication flow: verify OTP and get/create user
        
        Args:
            email: Email address
            otp_code: OTP code
            
        Returns:
            Tuple of (success: bool, user_data: Optional[dict], error_message: Optional[str])
        """
        # Verify OTP
        is_valid, error_msg = await self.verify_otp(email, otp_code)
        if not is_valid:
            return False, None, error_msg
        
        # Get or create user
        try:
            user = await self.get_or_create_user(email)
            return True, user, None
        except Exception as e:
            return False, None, f"Error creating user: {str(e)}"
