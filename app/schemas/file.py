"""File upload schemas"""

from typing import Optional
from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response schema for file upload"""
    success: bool
    message: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
