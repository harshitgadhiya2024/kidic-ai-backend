"""User Pydantic schemas for request/response validation"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    profile_picture: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user API response"""
    id: str
    email: str
    username: str
    profile_picture: Optional[str] = None
    credits: int
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class UserInDB(UserBase):
    """Schema for user stored in database"""
    id: str
    profile_picture: Optional[str] = None
    credits: int = 10
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
