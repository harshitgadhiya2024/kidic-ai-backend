"""Authentication endpoints"""

import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.dependencies import get_db, get_current_user
from app.core.security import verify_token
from app.models.photoshoot_generation import PhotoshootGenerationModel
from app.models.credit_transaction import CreditTransactionModel
from app.schemas.auth import (
    SendOTPRequest,
    VerifyOTPRequest,
    OTPResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from typing import Optional
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=OTPResponse, status_code=status.HTTP_200_OK)
async def login(
    request: SendOTPRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Login endpoint - Send OTP to email address
    
    - **email**: Email address to send OTP to
    
    This is the first step in the authentication flow.
    An OTP will be sent to the provided email address.
    Email is sent in the background for faster response.
    """
    auth_service = AuthService(db)
    
    success, message = await auth_service.send_otp(request.email, background_tasks)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
    
    return OTPResponse(
        message="OTP is being sent to your email. Please check your inbox.",
        email=request.email
    )


@router.post("/resend-otp", response_model=OTPResponse, status_code=status.HTTP_200_OK)
async def resend_otp(
    request: SendOTPRequest,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Resend OTP to email address
    
    - **email**: Email address to resend OTP to
    
    Use this endpoint if the user didn't receive the OTP or if it expired.
    Email is sent in the background for faster response.
    """
    auth_service = AuthService(db)
    
    success, message = await auth_service.send_otp(request.email, background_tasks)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
    
    return OTPResponse(
        message="OTP is being resent to your email. Please check your inbox.",
        email=request.email
    )


@router.post("/verify-otp", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def verify_otp(
    request: VerifyOTPRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Verify OTP and authenticate user
    
    - **email**: Email address
    - **otp_code**: 6-digit OTP code
    
    Returns JWT tokens and user information.
    If user doesn't exist, creates a new user account.
    """
    auth_service = AuthService(db)
    
    # Authenticate user (verify OTP and get/create user)
    success, user, error_msg = await auth_service.authenticate_user(
        email=request.email,
        otp_code=request.otp_code
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Create tokens
    tokens = await auth_service.create_tokens(user["id"])
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user=user
    )


@router.get("/me", response_model=dict, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get current authenticated user information

    Requires valid JWT access token in Authorization header.
    Returns user profile along with total photoshoots generated and total credits used.
    """
    try:
        user_id = current_user.get("id")

        generations_collection = db[PhotoshootGenerationModel.COLLECTION_NAME]
        credit_transactions_collection = db[CreditTransactionModel.COLLECTION_NAME]

        # Run both counts in parallel
        total_photoshoots, credits_used_agg = await asyncio.gather(
            generations_collection.count_documents({"user_id": user_id}),
            credit_transactions_collection.aggregate([
                {"$match": {"user_id": user_id, "type": CreditTransactionModel.TYPE_DEBIT}},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(length=1)
        )

        total_credits_used = credits_used_agg[0]["total"] if credits_used_agg else 0

        return {
            **current_user,
            "total_photoshoots_generated": total_photoshoots,
            "total_credits_used": total_credits_used,
        }

    except Exception as e:
        logger.error(f"Error fetching user info for {current_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information"
        )


@router.patch("/me", response_model=dict, status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    username: Optional[str] = None,
    profile_picture: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update current user's profile
    
    - **username**: New username (optional, 3-50 characters)
    - **profile_picture**: New profile picture URL (optional)
    
    Requires authentication. At least one field must be provided.
    """
    from bson import ObjectId
    from app.models import UserModel
    
    # Check if at least one field is provided
    if username is None and profile_picture is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one field (username or profile_picture) must be provided"
        )
    
    # Validate username if provided
    if username is not None:
        if len(username) < 3 or len(username) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be between 3 and 50 characters"
            )
    
    # Build update data
    update_data = {}
    if username is not None:
        update_data["username"] = username
    if profile_picture is not None:
        update_data["profile_picture"] = profile_picture
    
    try:
        # Update user in database
        users_collection = db[UserModel.COLLECTION_NAME]
        
        result = await users_collection.update_one(
            {"_id": ObjectId(current_user["id"])},
            UserModel.update_user_document(**update_data)
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found or no changes made"
            )
        
        # Get updated user
        updated_user = await users_collection.find_one(
            {"_id": ObjectId(current_user["id"])}
        )
        
        logger.info(f"User profile updated: {current_user['id']}")
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": UserModel.serialize_user(updated_user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating profile: {str(e)}"
        )


@router.post("/refresh", response_model=dict, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    
    Returns a new access token
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Create new access token
    auth_service = AuthService(db)
    tokens = await auth_service.create_tokens(user_id)
    
    return {
        "access_token": tokens["access_token"],
        "token_type": tokens["token_type"]
    }
