"""Authentication Pydantic schemas for request/response validation"""

from pydantic import BaseModel, EmailStr, Field


class SendOTPRequest(BaseModel):
    """Request schema for sending OTP"""
    email: EmailStr = Field(..., description="Email address to send OTP to")


class VerifyOTPRequest(BaseModel):
    """Request schema for verifying OTP"""
    email: EmailStr = Field(..., description="Email address")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")


class OTPResponse(BaseModel):
    """Response schema after sending OTP"""
    message: str
    email: str


class TokenResponse(BaseModel):
    """Response schema with JWT tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing access token"""
    refresh_token: str = Field(..., description="Refresh token")
