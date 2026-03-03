"""Contact Us Pydantic schemas"""

from pydantic import BaseModel, Field


class ContactUsRequest(BaseModel):
    """Request schema for submitting a contact us message"""
    message: str = Field(..., min_length=1, description="Message from the user")
    subject: str = Field(..., min_length=1, description="Subject of the message")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, I have a question about the product.",
                "subject": "question"
            }
        }


class ContactUsResponse(BaseModel):
    """Response schema for a contact us record"""
    id: str
    user_id: str
    message: str
    subject: str
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ContactUsCreateResponse(BaseModel):
    """Response schema for contact us creation endpoint"""
    success: bool
    message: str
    data: ContactUsResponse
