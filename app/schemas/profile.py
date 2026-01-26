"""User profile schemas"""

from typing import Optional
from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username (3-50 characters)")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "john_doe",
                "profile_picture": "https://example.com/profile.jpg"
            }
        }


class UpdateProfileResponse(BaseModel):
    """Response schema for profile update"""
    success: bool
    message: str
    user: dict
