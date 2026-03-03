"""Template Pydantic schemas"""

from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class CreateTemplateRequest(BaseModel):
    """Request schema for creating a template"""
    main_image_url: str = Field(..., description="Main image URL")
    pass_image_url: str = Field(..., description="Pass image URL")
    pose_details: str = Field(..., description="Pose details description")
    cloths_details: str = Field(..., description="Clothes details description")
    category: str = Field(..., description="template category")
    aspect_ratio: str = Field(..., description="Aspect ratio (e.g., '16:9', '1:1', '4:3')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "main_image_url": "https://example.com/main-image.jpg",
                "pass_image_url": "https://example.com/pass-image.jpg",
                "pose_details": "Standing pose with arms crossed",
                "cloths_details": "Casual t-shirt and jeans",
                "category": "Modern",
                "aspect_ratio": "16:9"
            }
        }


class UpdateTemplateRequest(BaseModel):
    """Request schema for updating a template"""
    main_image_url: Optional[str] = Field(None, description="Main image URL")
    pass_image_url: Optional[str] = Field(None, description="Pass image URL")
    pose_details: Optional[str] = Field(None, description="Pose details description")
    cloths_details: Optional[str] = Field(None, description="Clothes details description")
    category: str = Field(..., description="template category")
    aspect_ratio: Optional[str] = Field(None, description="Aspect ratio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "pose_details": "Updated pose description",
                "cloths_details": "Updated clothes description",
                "category": "Modern"
            }
        }


class TemplateResponse(BaseModel):
    """Response schema for template"""
    id: str
    main_image_url: str
    pass_image_url: str
    pose_details: str
    cloths_details: str
    aspect_ratio: str
    category: str
    is_active: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Response schema for list of templates"""
    total: int
    templates: list
