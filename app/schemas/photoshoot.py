"""Photoshoot Generation Pydantic schemas"""

from typing import Optional
from pydantic import BaseModel, Field


class GeneratePhotoshootRequest(BaseModel):
    """Request schema for generating a photoshoot (template_id only, kid_image via form-data)"""
    template_id: str = Field(..., description="Template ID to use for generation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "507f1f77bcf86cd799439011"
            }
        }


class PhotoshootGenerationResponse(BaseModel):
    """Response schema for photoshoot generation"""
    id: str
    user_id: str
    template_id: str
    kid_image_url: str
    task_id: Optional[str] = None
    is_favorite: bool = False
    model_used: Optional[str] = None
    status: str
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class PhotoshootGenerationListResponse(BaseModel):
    """Response schema for list of photoshoot generations"""
    total: int
    generations: list


class GeneratePhotoshootResponse(BaseModel):
    """Response schema for generate photoshoot endpoint"""
    success: bool
    message: str
    generation: PhotoshootGenerationResponse

